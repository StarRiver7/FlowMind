"""Hybrid Search — dense vector + BM25 keyword fusion retrieval.

Combines:
  1. Dense retrieval (Milvus vector search with BGE-M3)
  2. BM25 keyword search (lexical matching with jieba)
  3. Weighted fusion (configurable vector/keyword weights)
  4. Metadata filtering (department, space, visibility)

Now delegates to DenseRetriever + SparseRetriever + ScoreFusion
for cleaner separation of concerns.

Default weights: 70% vector, 30% keyword.
"""

import time
from typing import Optional

from app.rag.retrieval.dense_retriever import dense_retriever
from app.rag.retrieval.sparse_retriever import sparse_retriever
from app.rag.retrieval.score_fusion import score_fusion, ScoreFusion
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class HybridSearch:
    """InternSU hybrid search: vector + BM25 with metadata filtering.

    Delegates to:
      - DenseRetriever for vector search
      - SparseRetriever for BM25 keyword search
      - ScoreFusion for weighted result merging

    Usage:
        hs = HybridSearch()
        results = await hs.search(
            query="考勤制度",
            top_k=20,
            final_k=5,
            user_id=1,
            department_id=10,
            space_ids=[1, 2],
        )
    """

    def __init__(
        self,
        vector_weight: float = None,
        keyword_weight: float = None,
    ):
        self._vector_weight = vector_weight or settings.hybrid_weight_vector
        self._keyword_weight = keyword_weight or settings.hybrid_weight_keyword
        self._dense = dense_retriever
        self._sparse = sparse_retriever
        self._fusion = ScoreFusion(
            dense_weight=self._vector_weight,
            sparse_weight=self._keyword_weight,
        )

    async def search(
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
    ) -> list[dict]:
        """Execute hybrid search with full metadata filtering.

        Pipeline:
          1. Dense vector retrieval (BGE-M3 + Milvus)
          2. Sparse BM25 keyword search
          3. Weighted fusion
          4. Deduplicate + threshold filter

        Returns:
            Ranked list of search hits with scores and metadata.
        """
        start = time.time()

        # Phase 1: Dense retrieval
        dense_results = await self._dense.retrieve(
            query,
            top_k=top_k,
            score_threshold=0.0,  # Get all, filter after fusion
            user_id=user_id,
            department_id=department_id,
            space_ids=space_ids,
            document_ids=document_ids,
        )

        # Phase 2: Sparse BM25 retrieval
        sparse_results = self._sparse.search(
            query,
            dense_results if dense_results else [],
            top_k=top_k,
        )

        # Phase 3: Weighted fusion
        fused = self._fusion.fuse_weighted(dense_results, sparse_results)

        # Phase 4: Deduplicate + filter
        fused = self._fusion.deduplicate(fused)
        fused = [r for r in fused if r.get("score", 0) >= score_threshold]
        fused = fused[:final_k]

        elapsed = int((time.time() - start) * 1000)
        logger.info(
            f"[HybridSearch] '{query[:50]}': dense={len(dense_results)}, "
            f"sparse={len(sparse_results)}, fused={len(fused)} in {elapsed}ms"
        )
        return fused

    @property
    def vector_weight(self) -> float:
        return self._vector_weight

    @vector_weight.setter
    def vector_weight(self, value: float):
        self._vector_weight = value
        self._fusion._dense_w = value

    @property
    def keyword_weight(self) -> float:
        return self._keyword_weight

    @keyword_weight.setter
    def keyword_weight(self, value: float):
        self._keyword_weight = value
        self._fusion._sparse_w = value


hybrid_search = HybridSearch()
