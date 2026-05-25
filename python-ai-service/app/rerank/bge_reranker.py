"""
BGE-Reranker — cross-encoder relevance scoring.

Uses BGE-Reranker-v2-m3 for high-precision relevance re-ranking
of retrieval results before final context assembly.
"""
import time
from typing import Optional
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class BGEReranker:
    """Cross-encoder re-ranker using BAAI/bge-reranker-v2-m3.

    Re-ranks retrieved chunks by computing fine-grained relevance
    scores between query and each candidate document.
    """

    def __init__(self, model_name: str | None = None):
        self._model = None
        self._model_name = model_name or settings.bge_reranker_model

    async def _ensure_model(self):
        if self._model is not None:
            return self._model
        if self._model is False:  # Failed to load previously
            return None

        logger.info(f"Loading reranker model: {self._model_name}...")
        start = time.time()

        try:
            from FlagEmbedding import FlagReranker
            self._model = FlagReranker(
                self._model_name,
                use_fp16=settings.bge_use_fp16,
            )
        except (ImportError, Exception) as e:
            logger.warning(f"Reranker not available: {e}. Reranking will be skipped.")
            self._model = False  # Mark as failed
            return None

        elapsed = time.time() - start
        logger.info(f"Reranker loaded in {elapsed:.1f}s")
        return self._model

    async def rerank(
        self,
        query: str,
        chunks: list[dict],
        *,
        top_n: int | None = None,
    ) -> list[dict]:
        """Re-rank chunks by relevance to query."""
        if not chunks:
            return []

        top_n = top_n or settings.rerank_top_n
        top_n = min(top_n, len(chunks))
        model = await self._ensure_model()

        if model is None:
            # Reranker unavailable: return as-is sorted by original score
            chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
            return chunks[:top_n]
        start = time.time()

        # Create query-document pairs
        pairs = [[query, chunk["content"]] for chunk in chunks]

        # Compute relevance scores
        scores = model.compute_score(pairs, normalize=True)

        # Handle single score case
        if isinstance(scores, float):
            scores = [scores]

        # Attach rerank scores
        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[i]) if i < len(scores) else 0.0
            # Combined score: original * rerank
            chunk["combined_score"] = chunk.get("score", 0.5) * chunk["rerank_score"]

        # Sort by combined score
        chunks.sort(key=lambda x: x.get("combined_score", x.get("rerank_score", 0)), reverse=True)

        elapsed = (time.time() - start) * 1000
        logger.debug(f"Reranked {len(chunks)} chunks → top {top_n} in {elapsed:.0f}ms")

        return chunks[:top_n]


bge_reranker = BGEReranker()
