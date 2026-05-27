"""Rerank Score — composite scoring for re-ranked results.

Combines multiple signals into a final relevance score:

  final_score = α · retrieval_score + β · rerank_score + γ · metadata_bonus

Weights are dynamically adjustable per query type.
"""

from typing import Optional
from dataclasses import dataclass, field
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScoreConfig:
    """Configuration for composite score weights."""
    retrieval_weight: float = 0.40   # Original hybrid retrieval score
    rerank_weight: float = 0.50      # CrossEncoder semantic score
    metadata_weight: float = 0.10    # Metadata bonuses (title, dept, etc.)

    def __post_init__(self):
        total = self.retrieval_weight + self.rerank_weight + self.metadata_weight
        if abs(total - 1.0) > 0.001:
            logger.warning(
                f"[ScoreConfig] Weights sum to {total}, expected 1.0. Normalizing."
            )
            self.retrieval_weight /= total
            self.rerank_weight /= total
            self.metadata_weight /= total


class RerankScorer:
    """Composite score calculator for re-ranked results.

    Combines:
      - original retrieval score (from hybrid search)
      - cross-encoder relevance score
      - metadata bonuses
    into a single calibrated relevance score [0, 1].
    """

    def __init__(self, config: Optional[ScoreConfig] = None):
        self._config = config or ScoreConfig()

    def compute(
        self,
        retrieval_score: float,
        rerank_score: float,
        metadata_boost: float = 0.0,
    ) -> float:
        """Compute composite final score.

        Args:
            retrieval_score: original hybrid retrieval score [0, 1]
            rerank_score: cross-encoder relevance score [0, 1]
            metadata_boost: additional metadata bonus [0, 0.15]

        Returns:
            Final calibrated score [0, 1]
        """
        final = (
            self._config.retrieval_weight * retrieval_score +
            self._config.rerank_weight * rerank_score +
            self._config.metadata_weight * metadata_boost
        )
        return round(min(1.0, max(0.0, final)), 6)

    def compute_batch(
        self,
        chunks: list[dict],
        *,
        rerank_key: str = "rerank_score",
        retrieval_key: str = "score",
        metadata_key: str = "metadata_boost",
    ) -> list[dict]:
        """Compute composite scores for a batch of chunks.

        Adds/updates 'composite_score' and 'score' on each chunk.
        """
        for c in chunks:
            retrieval = c.get(retrieval_key, 0)
            rerank = c.get(rerank_key, retrieval)  # Fallback to retrieval
            metadata = c.get(metadata_key, 0)

            composite = self.compute(retrieval, rerank, metadata)

            c["composite_score"] = composite
            c["score"] = composite  # Update primary score

        # Re-sort
        chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        return chunks

    def compute_scores_array(
        self,
        retrieval_scores: list[float],
        rerank_scores: list[float],
        metadata_boosts: Optional[list[float]] = None,
    ) -> list[float]:
        """Compute composite scores from parallel arrays."""
        if metadata_boosts is None:
            metadata_boosts = [0.0] * len(retrieval_scores)

        return [
            self.compute(r, c, m)
            for r, c, m in zip(retrieval_scores, rerank_scores, metadata_boosts)
        ]

    @property
    def config(self) -> ScoreConfig:
        return self._config

    def adjust_weights(
        self,
        retrieval: Optional[float] = None,
        rerank: Optional[float] = None,
        metadata: Optional[float] = None,
    ):
        """Dynamically adjust score weights."""
        if retrieval is not None:
            self._config.retrieval_weight = retrieval
        if rerank is not None:
            self._config.rerank_weight = rerank
        if metadata is not None:
            self._config.metadata_weight = metadata


rerank_scorer = RerankScorer()
