"""Hybrid Search — dense vector + BM25 keyword fusion retrieval.

Combines:
  1. Dense retrieval (Milvus vector search with BGE-M3)
  2. BM25 keyword search (lexical matching)
  3. Weighted fusion (configurable vector/keyword weights)
  4. Metadata filtering (department, space, visibility)

Default weights: 70% vector, 30% keyword.
"""

import time
from typing import Optional
from rank_bm25 import BM25Okapi

from app.rag.vector_store.milvus_client import milvus_client
from app.rag.vector_store.metadata_filter import metadata_filter
from app.rag.embedding.embedding_service import embedding_service
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class HybridSearch:
    """Enterprise hybrid search: vector + BM25 with metadata filtering."""

    def __init__(
        self,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        self._vector_weight = vector_weight
        self._keyword_weight = keyword_weight

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
          1. Embed query → query vector
          2. Build access filter → metadata constraint
          3. Vector search (Milvus) → dense results
          4. BM25 keyword search → sparse results
          5. Weighted fusion → ranked results
          6. Deduplicate + threshold filter

        Returns:
            Ranked list of search hits with scores and metadata.
        """
        start = time.time()

        # Phase 1: Embed query
        await embedding_service.ensure_ready()
        query_vector = await embedding_service.embed_query(query)

        # Phase 2: Build access filter
        access_filter = metadata_filter.build_combined_filter(
            user_id=user_id,
            department_id=department_id,
            space_ids=space_ids,
            document_ids=document_ids,
        )

        # Phase 3: Vector search
        vector_results = milvus_client.search(
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=0.0,  # Get all, filter after fusion
            filter_expr=access_filter,
        )

        # Phase 4: BM25 keyword search
        bm25_results = self._bm25_search(query, vector_results, top_k)

        # Phase 5: Weighted fusion
        fused = self._fuse_results(
            vector_results, bm25_results,
            self._vector_weight, self._keyword_weight,
        )

        # Phase 6: Filter + limit
        fused = [r for r in fused if r.get("score", 0) >= score_threshold]
        fused = fused[:final_k]

        elapsed = int((time.time() - start) * 1000)
        logger.info(
            f"[HybridSearch] '{query[:50]}': vector={len(vector_results)}, "
            f"bm25={len(bm25_results)}, fused={len(fused)} in {elapsed}ms"
        )
        return fused

    def _bm25_search(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 20,
    ) -> list[dict]:
        """BM25 keyword search over candidates."""
        if not candidates:
            return []

        corpus = [c.get("content", "") for c in candidates]
        tokenized = [self._tokenize(doc) for doc in corpus]
        bm25 = BM25Okapi(tokenized)

        scores = bm25.get_scores(self._tokenize(query))
        max_score = max(scores) if scores and max(scores) > 0 else 1.0

        results = []
        for i, score in enumerate(scores):
            if score > 0:
                c = dict(candidates[i])
                c["bm25_score"] = float(score / max_score)
                results.append(c)

        results.sort(key=lambda x: x["bm25_score"], reverse=True)
        return results[:top_k]

    def _fuse_results(
        self,
        vector_results: list[dict],
        bm25_results: list[dict],
        vec_w: float,
        kw_w: float,
    ) -> list[dict]:
        """Weighted fusion by milvus_pk."""
        id_map = {}
        for r in vector_results:
            pk = r.get("milvus_pk")
            if pk is not None:
                id_map[pk] = {"vec": r.get("score", 0), "data": r}
        for r in bm25_results:
            pk = r.get("milvus_pk")
            if pk is not None:
                if pk in id_map:
                    id_map[pk]["kw"] = r.get("bm25_score", 0)
                else:
                    id_map[pk] = {"vec": 0, "kw": r.get("bm25_score", 0), "data": r}

        fused = []
        for pk, scores in id_map.items():
            vec_s = scores.get("vec", 0)
            kw_s = scores.get("kw", 0)
            combined = vec_s * vec_w + kw_s * kw_w
            result = dict(scores["data"])
            result["score"] = combined
            result["vector_score"] = vec_s
            result["keyword_score"] = kw_s
            fused.append(result)

        fused.sort(key=lambda x: x["score"], reverse=True)
        return fused

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re
        return re.findall(r"\w+", text.lower())


hybrid_search = HybridSearch()
