"""Retrieval Context — build LLM-ready context from retrieval results.

Transforms ranked search hits into formatted context strings
with source citations, token budget control, and deduplication.
"""

from typing import Optional
from app.rag.retrieval.source_builder import source_builder
from app.core.logger import get_logger

logger = get_logger(__name__)

# Default token budget for RAG context
DEFAULT_MAX_TOKENS = 3000
# Approximate chars per token for Chinese + English mixed text
CHARS_PER_TOKEN = 2.0


class RetrievalContext:
    """Build formatted context from search results for LLM consumption."""

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self._max_tokens = max_tokens

    def build(
        self,
        chunks: list[dict],
        *,
        query: str = "",
        max_tokens: Optional[int] = None,
        include_scores: bool = True,
    ) -> dict:
        """Build formatted RAG context from search results.

        Args:
            chunks: ranked search results
            query: original user query (for logging)
            max_tokens: override default token budget
            include_scores: include relevance scores in output

        Returns:
            {
                "context_text": str,      # formatted context for LLM
                "sources": [dict],        # structured source citations
                "total_chunks": int,      # total chunks considered
                "total_chars": int,       # total chars in context
                "truncated": bool,         # whether context was truncated
            }
        """
        max_tokens = max_tokens or self._max_tokens
        max_chars = int(max_tokens * CHARS_PER_TOKEN)

        sources = source_builder.build_batch(chunks)
        sources = source_builder.deduplicate_sources(sources)

        # Build context
        parts = []
        total_chars = 0
        truncated = False
        included_sources = []

        for i, src in enumerate(sources):
            chunk_text = src["content"]
            header = f"[Source {i+1}]"

            if include_scores:
                header += f" (relevance: {src['score']:.2f})"

            if src.get("document_name"):
                header += f" from {src['document_name']}"
            if src.get("page_number") and src["page_number"] > 0:
                header += f" page {src['page_number']}"

            entry = f"{header}\n{chunk_text}"

            # Token budget check
            entry_chars = len(entry)
            if total_chars + entry_chars > max_chars and i > 0:
                truncated = True
                logger.debug(
                    f"[RetrievalContext] Truncated at source {i}/{len(sources)} "
                    f"({total_chars}/{max_chars} chars)"
                )
                break

            parts.append(entry)
            total_chars += entry_chars
            included_sources.append(src)

        context_text = "\n\n---\n\n".join(parts)

        result = {
            "context_text": context_text,
            "sources": included_sources,
            "total_chunks": len(sources),
            "included_chunks": len(included_sources),
            "total_chars": total_chars,
            "truncated": truncated,
        }

        logger.debug(
            f"[RetrievalContext] Built context: {len(included_sources)}/{len(sources)} "
            f"sources, {total_chars} chars, truncated={truncated}"
        )
        return result

    def build_compact(self, chunks: list[dict], max_chunks: int = 5) -> str:
        """Build a compact context with only the top-N sources (no scores)."""
        sources = source_builder.build_batch(chunks[:max_chunks])
        parts = []
        for i, src in enumerate(sources):
            parts.append(f"[{i+1}] {src['content']}")
        return "\n\n".join(parts)


retrieval_context = RetrievalContext()
