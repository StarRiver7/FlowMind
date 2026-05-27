"""Sparse Retriever — BM25 keyword search with Chinese tokenization.

Features:
  - BM25 Okapi scoring
  - Jieba Chinese word segmentation
  - Title/heading boost
  - Score normalization to [0, 1]
"""

import time
import re
import numpy as np
from typing import Optional
from rank_bm25 import BM25Okapi
from app.core.logger import get_logger

logger = get_logger(__name__)

# Try jieba for Chinese, fallback to regex
try:
    import jieba
    _HAS_JIEBA = True
except ImportError:
    _HAS_JIEBA = False


class SparseRetriever:
    """BM25 keyword retriever with Chinese tokenization support."""

    def __init__(self):
        self._corpus_cache: dict[int, tuple[list[str], BM25Okapi]] = {}

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text for BM25 indexing."""
        if _HAS_JIEBA:
            tokens = list(jieba.cut(text.lower()))
            return [t.strip() for t in tokens if len(t.strip()) >= 1]
        else:
            return re.findall(r"[\u4e00-\u9fff]+|\w+", text.lower())

    def build_index(self, candidates: list[dict]) -> tuple[list[str], BM25Okapi]:
        """Build BM25 index from candidate documents."""
        if not candidates:
            return [], None

        corpus = []
        for c in candidates:
            content = c.get("content", "")
            title_path = c.get("title_path", "")
            text = content
            if title_path:
                text = f"{title_path} {title_path} {content}"
            corpus.append(text)

        tokenized = [self.tokenize(doc) for doc in corpus]
        bm25 = BM25Okapi(tokenized)
        return tokenized, bm25

    def search(
        self,
        query: str,
        candidates: list[dict],
        *,
        top_k: int = 20,
        title_boost: float = 2.0,
    ) -> list[dict]:
        """BM25 keyword search over candidates.

        Returns all candidates with normalized BM25 scores in [0, 1].
        Negative BM25 scores (common with small corpora) are kept —
        the score_fusion stage will handle final relevance weighting.
        """
        if not candidates:
            return []

        start = time.time()
        tokenized_corpus, bm25 = self.build_index(candidates)
        if bm25 is None:
            return []

        tokenized_query = self.tokenize(query)
        scores = bm25.get_scores(tokenized_query)

        if isinstance(scores, np.ndarray):
            score_list = scores.tolist()
        else:
            score_list = list(scores)

        # Normalize all scores to [0, 1]. BM25 scores can be negative;
        # we use the full range so relative ranking is preserved.
        if score_list:
            min_s = min(score_list)
            max_s = max(score_list)
            denom = max_s - min_s if max_s != min_s else 1.0
        else:
            min_s, max_s, denom = 0, 0, 1.0

        results = []
        for i, raw_score in enumerate(score_list):
            normalized = (raw_score - min_s) / denom

            # Title boost: if query tokens appear in title, boost score
            title_path = candidates[i].get("title_path", "")
            if title_path:
                title_tokens = set(self.tokenize(title_path))
                query_tokens = set(tokenized_query)
                if title_tokens & query_tokens:
                    normalized = min(1.0, normalized * title_boost)

            c = dict(candidates[i])
            c["bm25_score"] = normalized
            c["sparse_score"] = normalized
            results.append(c)

        results.sort(key=lambda x: x["bm25_score"], reverse=True)
        results = results[:top_k]

        elapsed = int((time.time() - start) * 1000)
        logger.debug(
            f"[SparseRetriever] '{query[:40]}': {len(results)} results in {elapsed}ms"
        )
        return results


sparse_retriever = SparseRetriever()
