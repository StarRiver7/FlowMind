"""Rerank Pipeline — full re-ranking orchestration.

Flow:
    TopK Retrieval Results
    ↓
    CrossEncoder Scoring (pairwise relevance)
    ↓
    Duplicate Filter (remove near-duplicates)
    ↓
    Composite Score Calculation
    ↓
    Sort + TopN
    ↓
    Reranked Results

Produces calibrated, deduplicated results where the most
semantically relevant chunks rank highest.
"""

import time
from typing import Optional, Callable
from app.rag.rerank.cross_encoder import cross_encoder, CrossEncoder
from app.rag.rerank.rerank_score import rerank_scorer, RerankScorer, ScoreConfig
from app.rag.rerank.duplicate_filter import duplicate_filter, DuplicateFilter
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class RerankPipeline:
    """Full re-ranking pipeline.

    Takes top-K retrieval results and produces a calibrated,
    deduplicated top-N list where the most semantically relevant
    chunks appear first.

    Usage:
        pipeline = RerankPipeline()
        reranked = await pipeline.rerank(
            query="请假制度",
            chunks=retrieval_results,
            top_n=5,
        )
    """

    def __init__(
        self,
        cross_encoder: Optional[CrossEncoder] = None,
        scorer: Optional[RerankScorer] = None,
        dup_filter: Optional[DuplicateFilter] = None,
    ):
        self._cross_encoder = cross_encoder or globals()["cross_encoder"]
        self._scorer = scorer or rerank_scorer
        self._dup_filter = dup_filter or duplicate_filter

    async def rerank(
        self,
        query: str,
        chunks: list[dict],
        *,
        top_n: Optional[int] = None,
        score_threshold: float = 0.3,
        dedup_strategy: str = "all",
        content_key: str = "content",
    ) -> list[dict]:
        """Execute full re-ranking pipeline.

        Args:
            query: original user query
            chunks: top-K retrieval results
            top_n: final result count (defaults to settings.rag_final_k)
            score_threshold: minimum composite score to keep
            dedup_strategy: "exact" | "prefix" | "jaccard" | "all"
            content_key: dict key for content text

        Returns:
            Re-ranked, deduplicated, score-calibrated results.
        """
        if not chunks:
            return []

        top_n = top_n or settings.rag_final_k
        start = time.time()
        original_count = len(chunks)

        # ── Phase 1: CrossEncoder Scoring ──
        contents = [c.get(content_key, "") for c in chunks]
        rerank_scores = self._cross_encoder.compute_scores(query, contents)

        for chunk, rs in zip(chunks, rerank_scores):
            chunk["rerank_score"] = rs
            chunk["cross_encoder_score"] = rs

        # ── Phase 2: Composite Scoring ──
        chunks = self._scorer.compute_batch(chunks)

        # Sort by composite score
        chunks.sort(key=lambda x: x.get("score", 0), reverse=True)

        # ── Phase 3: Duplicate Filter ──
        before_dedup = len(chunks)
        chunks = self._dup_filter.filter(chunks, strategy=dedup_strategy)

        # ── Phase 4: Threshold + TopN ──
        chunks = [c for c in chunks if c.get("score", 0) >= score_threshold]
        chunks = chunks[:top_n]

        elapsed = int((time.time() - start) * 1000)
        logger.info(
            f"[RerankPipeline] '{query[:40]}': "
            f"{original_count} → {before_dedup} → {len(chunks)} "
            f"in {elapsed}ms "
            f"(threshold={score_threshold}, top_n={top_n})"
        )

        return chunks

    def rerank_sync(
        self,
        query: str,
        chunks: list[dict],
        **kwargs,
    ) -> list[dict]:
        """Synchronous wrapper (for non-async contexts)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.rerank(query, chunks, **kwargs))

    @property
    def cross_encoder(self) -> CrossEncoder:
        return self._cross_encoder

    @property
    def scorer(self) -> RerankScorer:
        return self._scorer


rerank_pipeline = RerankPipeline()
