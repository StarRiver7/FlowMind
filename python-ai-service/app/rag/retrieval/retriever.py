"""Retriever — unified retrieval engine combining search, rank, context.

Single entry point for all RAG retrieval operations.
Orchestrates: hybrid search → rank → build context → build sources.
"""

import time
from typing import Optional
from dataclasses import dataclass, field

from app.rag.retrieval.hybrid_search import hybrid_search
from app.rag.retrieval.retrieval_ranker import retrieval_ranker
from app.rag.retrieval.retrieval_context import retrieval_context
from app.rag.retrieval.source_builder import source_builder
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """Complete retrieval result."""
    query: str
    chunks: list[dict] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    context_text: str = ""
    total_chunks: int = 0
    total_chars: int = 0
    elapsed_ms: int = 0
    truncated: bool = False


class Retriever:
    """Enterprise RAG retrieval engine.

    Usage:
        retriever = Retriever()
        result = await retriever.retrieve(
            query="员工考勤制度",
            user_id=1,
            department_id=10,
            space_ids=[1, 2],
        )
        # result.context_text → formatted context for LLM
        # result.sources → structured citations
    """

    def __init__(self):
        self._search = hybrid_search
        self._ranker = retrieval_ranker
        self._context = retrieval_context

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 20,
        final_k: int = 5,
        score_threshold: float = 0.3,
        user_id: int = 0,
        department_id: Optional[int] = None,
        space_ids: Optional[list[int]] = None,
        document_ids: Optional[list[int]] = None,
        build_context: bool = True,
        max_context_tokens: int = 3000,
    ) -> RetrievalResult:
        """Execute complete retrieval pipeline.

        Steps:
          1. Hybrid search (vector + BM25)
          2. Rank + dedup + filter
          3. Build sources
          4. Build LLM context

        Returns:
            RetrievalResult with chunks, sources, context_text
        """
        start = time.time()

        # Step 1: Hybrid search
        chunks = await self._search.search(
            query=query,
            top_k=top_k,
            final_k=final_k * 2,  # Get more for ranking
            score_threshold=0.0,    # Filter after ranking
            user_id=user_id,
            department_id=department_id,
            space_ids=space_ids,
            document_ids=document_ids,
        )

        # Step 2: Rank
        chunks = await self._ranker.rank(
            query, chunks,
            top_n=final_k,
            score_threshold=score_threshold,
        )

        # Step 3: Build sources
        sources = source_builder.build_batch(chunks)

        # Step 4: Build context
        ctx_result = {}
        if build_context and chunks:
            ctx_result = self._context.build(
                chunks,
                query=query,
                max_tokens=max_context_tokens,
            )

        elapsed = int((time.time() - start) * 1000)
        logger.info(
            f"[Retriever] '{query[:50]}': {len(chunks)} chunks, "
            f"{len(sources)} sources in {elapsed}ms"
        )

        return RetrievalResult(
            query=query,
            chunks=chunks,
            sources=sources,
            context_text=ctx_result.get("context_text", ""),
            total_chunks=ctx_result.get("included_chunks", len(chunks)),
            total_chars=ctx_result.get("total_chars", 0),
            elapsed_ms=elapsed,
            truncated=ctx_result.get("truncated", False),
        )

    async def retrieve_context_only(
        self,
        query: str,
        **kwargs,
    ) -> str:
        """Retrieve and return only the formatted context text."""
        result = await self.retrieve(query, **kwargs)
        return result.context_text


retriever = Retriever()
