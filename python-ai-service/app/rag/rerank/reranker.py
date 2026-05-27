"""Reranker — unified semantic re-ranking facade.

Delegates to the RerankPipeline (cross_encoder + scorer + dup_filter)
for enterprise-grade re-ranking.

This module replaces the basic score-based reranker in retrieval/reranker.py
with a full semantic re-ranking pipeline.

Architecture:
  CrossEncoder(query, chunk) → relevance_score
  RerankScorer → composite = α·retrieval + β·rerank + γ·metadata
  DuplicateFilter → remove near-duplicates
  → TopN calibrated results
"""

import time
from typing import Optional
from app.rag.rerank.rerank_pipeline import rerank_pipeline, RerankPipeline
from app.rag.rerank.cross_encoder import cross_encoder, CrossEncoder
from app.rag.rerank.rerank_score import rerank_scorer
from app.rag.rerank.duplicate_filter import duplicate_filter
from app.core.logger import get_logger

logger = get_logger(__name__)


class Reranker:
    """Enterprise semantic re-ranker.

    Produces calibrated relevance scores where the most
    semantically relevant chunks rank highest.

    Usage:
        reranker = Reranker()
        reranked = await reranker.rerank(query, chunks, top_n=5)

        # Load BGE-Reranker for true semantic scoring:
        reranker.load_semantic_model()
    """

    def __init__(self):
        self._pipeline = rerank_pipeline
        self._cross_encoder = cross_encoder
        self._scorer = rerank_scorer
        self._dup_filter = duplicate_filter

    async def rerank(
        self,
        query: str,
        chunks: list[dict],
        *,
        top_n: Optional[int] = None,
        score_threshold: float = 0.3,
        dedup_strategy: str = "all",
    ) -> list[dict]:
        """Re-rank retrieval results.

        Pipeline:
          1. CrossEncoder: compute pairwise (query, chunk) relevance
          2. Composite Score: merge retrieval + rerank + metadata
          3. Duplicate Filter: remove near-duplicates
          4. Threshold + TopN

        Args:
            query: original search query
            chunks: top-K retrieval results
            top_n: final result count
            score_threshold: minimum score to keep
            dedup_strategy: "exact" | "prefix" | "jaccard" | "all"

        Returns:
            Calibrated, deduplicated, sorted results.
        """
        return await self._pipeline.rerank(
            query=query,
            chunks=chunks,
            top_n=top_n,
            score_threshold=score_threshold,
            dedup_strategy=dedup_strategy,
        )

    def load_semantic_model(self, model_name: Optional[str] = None) -> bool:
        """Load BGE-Reranker for true CrossEncoder semantic scoring.

        Without this, the system uses a heuristic fallback.
        With BGE-Reranker loaded, scores reflect true semantic relevance.
        """
        if model_name:
            self._cross_encoder._model_name = model_name
        return self._cross_encoder.load()

    @property
    def is_semantic(self) -> bool:
        """Whether true semantic (transformer) reranking is active."""
        return self._cross_encoder.is_loaded

    def analyze_rerank(
        self,
        query: str,
        chunks: list[dict],
    ) -> list[dict]:
        """Analyze rerank behavior: show how scores changed.

        Returns comparison: retrieval_score → rerank_score → composite → delta
        """
        contents = [c.get("content", "") for c in chunks]
        rerank_scores = self._cross_encoder.compute_scores(query, contents)

        analysis = []
        for chunk, rs in zip(chunks, rerank_scores):
            orig = chunk.get("score", 0)
            composite = self._scorer.compute(orig, rs, chunk.get("metadata_boost", 0))
            analysis.append({
                "content_preview": chunk.get("content", "")[:80],
                "retrieval_score": round(orig, 4),
                "rerank_score": round(rs, 4),
                "composite_score": round(composite, 4),
                "delta": round(composite - orig, 4),
                "rank_change": 0,  # Caller should sort to determine
            })

        # Sort by composite and annotate rank changes
        analysis.sort(key=lambda x: x["composite_score"], reverse=True)
        for i, a in enumerate(analysis):
            a["new_rank"] = i + 1

        return analysis


reranker = Reranker()
