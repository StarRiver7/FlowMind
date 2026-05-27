"""Retrieval Context — build LLM-ready context from retrieval results.

Transforms ranked search hits into formatted context strings
with source citations, token budget control, chunk merge awareness,
and compact mode for short-form answers.
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
    """Build formatted context from search results for LLM consumption.

    Supports:
      - Standard context: full [Source N] blocks with scores
      - Compact mode: minimal formatting for short answers
      - Merge-aware: respects merge_count for source labeling
    """

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self._max_tokens = max_tokens

    def build(
        self,
        chunks: list[dict],
        *,
        query: str = "",
        max_tokens: Optional[int] = None,
        include_scores: bool = True,
        include_metadata: bool = True,
    ) -> dict:
        """Build formatted RAG context from search results.

        Args:
            chunks: ranked search results (may contain merged chunks)
            query: original user query (for logging)
            max_tokens: override default token budget
            include_scores: include relevance scores in output
            include_metadata: include document/page info in headers

        Returns:
            {
                "context_text": str,       # formatted context for LLM
                "sources": [dict],         # structured source citations
                "total_chunks": int,       # total chunks considered
                "included_chunks": int,    # chunks actually included
                "total_chars": int,        # total chars in context
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

            # Build header
            header_parts = [f"[Source {i + 1}]"]

            if include_scores:
                header_parts.append(f"(relevance: {src['score']:.2f})")

            if include_metadata:
                if src.get("document_name"):
                    header_parts.append(f"from {src['document_name']}")

                # Page info — handle page ranges for merged chunks
                page_range = src.get("page_range")
                if page_range and len(page_range) > 1:
                    header_parts.append(f"pages {page_range[0]}-{page_range[-1]}")
                elif src.get("page_number") and src["page_number"] > 0:
                    header_parts.append(f"page {src['page_number']}")

                # Knowledge base
                kb = src.get("knowledge_base")
                if kb:
                    header_parts.append(f"[{kb}]")

                # Merge indicator
                merge_count = src.get("merge_count", 1)
                if merge_count > 1:
                    header_parts.append(f"(merged {merge_count} chunks)")

            entry = f"{' '.join(header_parts)}\n{chunk_text}"

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

    def build_compact(
        self,
        chunks: list[dict],
        max_chunks: int = 5,
    ) -> str:
        """Build a compact context with only the top-N sources (no scores).

        Useful for short-form answers where token budget is tight.
        """
        sources = source_builder.build_batch(chunks[:max_chunks])
        parts = []
        for i, src in enumerate(sources):
            header = f"[{i + 1}]"
            if src.get("document_name"):
                header += f" {src['document_name']}"
            if src.get("page_number") and src["page_number"] > 0:
                header += f" p.{src['page_number']}"
            parts.append(f"{header}\n{src['content']}")
        return "\n\n".join(parts)

    def build_citation_only(
        self,
        chunks: list[dict],
    ) -> list[str]:
        """Build citation references only (no content), for inline source attribution."""
        sources = source_builder.build_batch(chunks)
        return [
            f"{s['document_name']} 第{s['page_number']}页"
            if s.get("page_number") and s["page_number"] > 0
            else s["document_name"]
            for s in sources
        ]


retrieval_context = RetrievalContext()
