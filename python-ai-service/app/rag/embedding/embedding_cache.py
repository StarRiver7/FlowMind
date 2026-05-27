"""Embedding Cache — hash-based cache to avoid redundant embeddings.

Caches embeddings by content SHA-256 hash.
Useful for:
  - Repeated queries
  - Overlapping chunks (same text in multiple documents)
  - Testing/development cycles
"""

import hashlib
import time
from typing import Optional
from collections import OrderedDict
from app.core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingCache:
    """In-memory LRU cache for embeddings.

    Caches by SHA-256 hash of content text.
    """

    def __init__(self, max_size: int = 10000):
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[list[float]]:
        key = self._hash(text)
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, text: str, vector: list[float]) -> None:
        key = self._hash(text)
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = vector
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = vector

    def put_batch(self, texts: list[str], vectors: list[list[float]]) -> None:
        for text, vec in zip(texts, vectors):
            self.put(text, vec)

    def get_batch(self, texts: list[str]) -> tuple[list[Optional[list[float]]], list[int]]:
        """Check cache for a batch of texts.

        Returns:
            (cached_vectors, missing_indices)
            cached_vectors[i] is None if not in cache.
        """
        cached = []
        missing = []
        for i, text in enumerate(texts):
            vec = self.get(text)
            if vec is not None:
                cached.append(vec)
            else:
                cached.append(None)
                missing.append(i)
        return cached, missing

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict:
        return {
            "size": self.size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self.hit_rate:.2%}",
        }

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("[EmbeddingCache] Cleared")


embedding_cache = EmbeddingCache()
