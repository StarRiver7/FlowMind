"""Retrieval Ranker — Rerank interface placeholder.

Current: score-based ranking only.
Future: BGE-Reranker integration for re-ranking top results.
"""

from typing import Optional
from app.core.logger import get_logger

logger = get_logger(__name__)


class RetrievalRanker:
    """Post-retrieval ranker.

    Current implementation: score-based sorting + dedup.
    Placeholder for future BGE-Reranker integration.
    """

    def __init__(self):
        self._reranker = None  # Future: BGE-Reranker

    async def rank(
        self,
        query: str,
        chunks: list[dict],
        *,
        top_n: Optional[int] = None,
        score_threshold: float = 0.3,
    ) -> list[dict]:
        """Rank and filter retrieval results.

        Args:
            query: original search query
            chunks: raw retrieval results with scores
            top_n: max results to return
            score_threshold: minimum score to keep

        Returns:
            Ranked and filtered results
        """
        # Deduplicate by content hash
        seen = set()
        unique = []
        for c in chunks:
            key = c.get("content", "")[:200]
            if key not in seen:
                seen.add(key)
                unique.append(c)

        # Filter by score
        filtered = [c for c in unique if c.get("score", 0) >= score_threshold]

        # Sort by score descending
        filtered.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Future: BGE-Reranker re-ranking here
        # if self._reranker:
        #     filtered = await self._reranker.rerank(query, filtered)

        if top_n:
            filtered = filtered[:top_n]

        return filtered

    async def is_reranker_available(self) -> bool:
        return self._reranker is not None


retrieval_ranker = RetrievalRanker()
