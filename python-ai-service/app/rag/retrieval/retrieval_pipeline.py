"""Retrieval Pipeline — full orchestrated retrieval engine.

Complete pipeline:
    User Query
    ↓ Query Rewrite (LLM expansion)
    ↓ Dense Retrieval (BGE-M3 vector search)
    ↓ Sparse Retrieval (BM25 keyword search)
    ↓ Score Fusion (weighted hybrid merge)
    ↓ Metadata Boost (title/recent/department)
    ↓ Rerank (CrossEncoder semantic reorder)
    ↓ Chunk Merge (adjacent context joining)
    ↓ Source Builder (citation formatting)
    ↓ Retrieval Context (LLM-ready text)

Every step produces a trace event for SSE streaming.
"""

import time
from typing import Optional
from dataclasses import dataclass, field

from app.rag.retrieval.query_rewrite import query_rewriter
from app.rag.retrieval.dense_retriever import dense_retriever
from app.rag.retrieval.sparse_retriever import sparse_retriever
from app.rag.retrieval.score_fusion import score_fusion
from app.rag.retrieval.metadata_boost import metadata_boost
from app.rag.retrieval.reranker import reranker
from app.rag.retrieval.chunk_merger import chunk_merger
from app.rag.retrieval.source_builder import source_builder
from app.rag.retrieval.retrieval_context import retrieval_context as rc_builder
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """Complete retrieval result."""
    query: str
    rewritten_query: str = ""
    chunks: list[dict] = field(default_factory=list)
    merged_chunks: list[dict] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    context_text: str = ""
    dense_count: int = 0
    sparse_count: int = 0
    fused_count: int = 0
    final_count: int = 0
    total_chars: int = 0
    elapsed_ms: int = 0
    truncated: bool = False
    traces: list[dict] = field(default_factory=list)


class RetrievalPipeline:
    """Orchestrated retrieval pipeline with full trace support.

    Usage:
        pipeline = RetrievalPipeline()
        result = await pipeline.retrieve(
            query="请假制度",
            user_id=1,
            department_id=10,
            space_ids=[1, 2],
        )
        # result.context_text → formatted context for LLM
        # result.sources → structured citations
        # result.traces → step-by-step events for SSE
    """

    def __init__(self):
        self._dense = dense_retriever
        self._sparse = sparse_retriever
        self._fusion = score_fusion
        self._boost = metadata_boost
        self._reranker = reranker
        self._merger = chunk_merger

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
        enable_rewrite: bool = True,
        enable_boost: bool = True,
        enable_rerank: bool = True,
        enable_merge: bool = True,
        build_context: bool = True,
        max_context_tokens: int = 3000,
        stream_traces: Optional[list[dict]] = None,
    ) -> RetrievalResult:
        """Execute the complete retrieval pipeline.

        If stream_traces is provided (a list reference), trace events
        are appended to it in real-time for SSE streaming.

        Returns:
            RetrievalResult with full metadata and traces.
        """
        start = time.time()
        traces: list[dict] = []
        if stream_traces is not None:
            stream_traces.clear()

        def _trace(step: str, detail: dict | None = None):
            event = {
                "step": step,
                "timestamp_ms": int((time.time() - start) * 1000),
            }
            if detail:
                event["detail"] = detail
            traces.append(event)
            if stream_traces is not None:
                stream_traces.append(dict(event))

        # ── Phase 1: Query Rewrite ──
        _trace("rewrite_query", {"original": query[:50]})
        rewritten = query
        if enable_rewrite:
            rewritten = await query_rewriter.rewrite(query)
            _trace("rewrite_query", {
                "original": query[:50],
                "rewritten": rewritten[:80],
            })
        else:
            _trace("rewrite_query", {"skipped": True})

        # ── Phase 2: Dense Retrieval ──
        _trace("dense_retrieval", {"query": rewritten[:50]})
        dense_results = await self._dense.retrieve(
            rewritten,
            top_k=top_k,
            score_threshold=0.0,  # Get all, filter after fusion
            user_id=user_id,
            department_id=department_id,
            space_ids=space_ids,
            document_ids=document_ids,
        )
        _trace("dense_retrieval", {"count": len(dense_results)})

        # ── Phase 3: Sparse Retrieval ──
        _trace("sparse_retrieval", {"query": rewritten[:50]})
        sparse_results = self._sparse.search(
            rewritten,
            dense_results if dense_results else [],
            top_k=top_k,
        )
        _trace("sparse_retrieval", {"count": len(sparse_results)})

        # ── Phase 4: Score Fusion ──
        _trace("score_fusion", {
            "dense_count": len(dense_results),
            "sparse_count": len(sparse_results),
            "method": "weighted",
            "weights": {
                "dense": self._fusion._dense_w,
                "sparse": self._fusion._sparse_w,
            },
        })
        fused = self._fusion.fuse_weighted(dense_results, sparse_results)
        fused = self._fusion.deduplicate(fused)
        _trace("score_fusion", {"fused_count": len(fused)})

        # ── Phase 5: Metadata Boost ──
        if enable_boost and fused:
            _trace("metadata_boost", {"count": len(fused)})
            fused = self._boost.apply(
                fused,
                query=rewritten,
                department_id=department_id,
            )
            _trace("metadata_boost", {"boosted": True})

        # ── Phase 6: Rerank ──
        if enable_rerank and fused:
            _trace("rerank", {"count": len(fused)})
            fused = await self._reranker.rerank(
                rewritten, fused,
                top_n=final_k * 2,  # Get extra for merge
                score_threshold=score_threshold,
            )
            _trace("rerank", {"count": len(fused)})

        # ── Phase 7: Chunk Merge ──
        if enable_merge and len(fused) > 1:
            _trace("chunk_merge", {"count": len(fused)})
            merged = self._merger.merge(fused)
            _trace("chunk_merge", {
                "before": len(fused),
                "after": len(merged),
            })
        else:
            merged = fused
            _trace("chunk_merge", {"skipped": True})

        # Limit to final_k
        merged = merged[:final_k]

        # ── Phase 8: Source Builder ──
        _trace("source_builder", {"count": len(merged)})
        sources = source_builder.build_batch(merged)
        sources = source_builder.deduplicate_sources(sources)
        _trace("source_builder", {"sources": len(sources)})

        # ── Phase 9: Retrieval Context ──
        ctx_result = {}
        if build_context and merged:
            _trace("context_builder", {"count": len(merged)})
            ctx_result = rc_builder.build(
                merged,
                query=query,
                max_tokens=max_context_tokens,
            )
            _trace("context_builder", {
                "chars": ctx_result.get("total_chars", 0),
                "truncated": ctx_result.get("truncated", False),
            })

        elapsed = int((time.time() - start) * 1000)
        _trace("complete", {"elapsed_ms": elapsed})

        logger.info(
            f"[RetrievalPipeline] '{query[:50]}': "
            f"dense={len(dense_results)} sparse={len(sparse_results)} "
            f"fused={len(fused)} merged={len(merged)} → {len(sources)} sources "
            f"in {elapsed}ms"
        )

        return RetrievalResult(
            query=query,
            rewritten_query=rewritten,
            chunks=fused,
            merged_chunks=merged,
            sources=sources,
            context_text=ctx_result.get("context_text", ""),
            dense_count=len(dense_results),
            sparse_count=len(sparse_results),
            fused_count=len(fused),
            final_count=len(merged),
            total_chars=ctx_result.get("total_chars", 0),
            elapsed_ms=elapsed,
            truncated=ctx_result.get("truncated", False),
            traces=traces,
        )

    async def retrieve_context_only(
        self,
        query: str,
        **kwargs,
    ) -> str:
        """Retrieve and return only the formatted context text."""
        result = await self.retrieve(query, **kwargs)
        return result.context_text

    async def search_raw(
        self,
        query: str,
        **kwargs,
    ) -> list[dict]:
        """Retrieve and return raw merged chunks only (no context building)."""
        result = await self.retrieve(query, build_context=False, **kwargs)
        return result.merged_chunks


retrieval_pipeline = RetrievalPipeline()
