"""Embedding Batch Processor — optimized batch embedding with cache.

Features:
  - Cache-first: check cache before computing
  - Batch sizing: auto-split large batches
  - Progress tracking: yield progress for each batch
  - Retry: exponential backoff on failure
"""

import time
import asyncio
from typing import Optional
from app.rag.embedding.bge_embedding import bge_embedding
from app.rag.embedding.embedding_cache import embedding_cache
from app.core.logger import get_logger

logger = get_logger(__name__)

DEFAULT_BATCH_SIZE = 32
MAX_RETRIES = 3


class EmbeddingBatchProcessor:
    """Batch embedding processor with caching and retry."""

    def __init__(self, batch_size: int = DEFAULT_BATCH_SIZE):
        self._batch_size = batch_size
        self._bge = bge_embedding
        self._cache = embedding_cache

    async def embed_batch(
        self,
        texts: list[str],
        *,
        use_cache: bool = True,
        on_progress: Optional[callable] = None,
    ) -> list[list[float]]:
        """Embed a batch of texts with cache + retry.

        Args:
            texts: list of text strings to embed
            use_cache: whether to check cache first
            on_progress: optional callback(batch_num, total_batches) for progress

        Returns:
            list of embedding vectors in same order as texts
        """
        if not texts:
            return []

        total = len(texts)
        start_time = time.time()

        # Phase 1: Cache lookup
        results: list[Optional[list[float]]] = [None] * total
        missing_indices: list[int] = []

        if use_cache:
            cached, missing_indices = self._cache.get_batch(texts)
            for i, vec in enumerate(cached):
                if vec is not None:
                    results[i] = vec

        if not missing_indices:
            elapsed = int((time.time() - start_time) * 1000)
            logger.debug(f"[EmbedBatch] All {total} texts from cache in {elapsed}ms")
            return [r for r in results if r is not None]  # type narrowing

        # Phase 2: Compute missing embeddings in sub-batches
        missing_texts = [texts[i] for i in missing_indices]
        num_batches = (len(missing_texts) + self._batch_size - 1) // self._batch_size

        for batch_num in range(num_batches):
            start_idx = batch_num * self._batch_size
            end_idx = min(start_idx + self._batch_size, len(missing_texts))
            batch_texts = missing_texts[start_idx:end_idx]

            if on_progress:
                on_progress(batch_num + 1, num_batches)

            # Compute with retry
            vectors = await self._embed_with_retry(batch_texts)

            # Store in results and cache
            for j, (text, vec) in enumerate(zip(batch_texts, vectors)):
                global_idx = missing_indices[start_idx + j]
                results[global_idx] = vec
                if use_cache:
                    self._cache.put(text, vec)

        elapsed = int((time.time() - start_time) * 1000)
        cache_hits = total - len(missing_indices)
        logger.info(
            f"[EmbedBatch] {total} texts: {cache_hits} cache hits, "
            f"{len(missing_indices)} computed in {elapsed}ms "
            f"(cache hit rate: {self._cache.hit_rate:.1%})"
        )

        return [r for r in results if r is not None]

    async def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Embed with exponential backoff retry."""
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return await self._bge.embed_texts(texts)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    logger.warning(f"[EmbedBatch] Retry {attempt+1}/{MAX_RETRIES} in {wait}s: {e}")
                    await asyncio.sleep(wait)
        raise RuntimeError(f"Embedding failed after {MAX_RETRIES} retries: {last_error}")


embedding_batch = EmbeddingBatchProcessor()
