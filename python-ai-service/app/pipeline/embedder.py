"""
Embedding Engine — BGE model wrapper with batch optimization.

Supports BGE-M3 (1024-dim) and BGE-small (512-dim).
Features: dense embeddings, optional sparse weights, FP16 acceleration.
"""
import time
import numpy as np
from typing import Optional
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingEngine:
    """BGE-M3 embedding engine with automatic batch processing."""

    BATCH_SIZE = 32  # Optimal batch size for BGE-M3

    def __init__(self):
        self._model = None
        self._model_name = settings.bge_model_name
        self._dim = settings.embedding_dim
        self._device = settings.bge_device

    async def _ensure_model(self):
        if self._model is not None:
            return self._model

        logger.info(f"Loading embedding model: {self._model_name} on {self._device}...")
        start = time.time()

        try:
            from FlagEmbedding import FlagModel, BGEM3FlagModel
        except ImportError:
            raise ImportError(
                "FlagEmbedding not installed. Run: pip install FlagEmbedding"
            )

        # Auto-detect model type: M3 models use BGEM3FlagModel, others use FlagModel
        is_m3 = "m3" in self._model_name.lower()
        try:
            if is_m3:
                self._model = BGEM3FlagModel(
                    self._model_name,
                    use_fp16=settings.bge_use_fp16,
                    device=self._device,
                )
            else:
                self._model = FlagModel(
                    self._model_name,
                    use_fp16=settings.bge_use_fp16,
                    normalize_embeddings=True,
                )
        except Exception as e:
            # Fallback: try FlagModel for any model
            logger.warning(f"BGEM3FlagModel failed, trying FlagModel: {e}")
            self._model = FlagModel(
                self._model_name,
                use_fp16=settings.bge_use_fp16,
                normalize_embeddings=True,
            )

        elapsed = time.time() - start
        logger.info(f"Embedding model loaded in {elapsed:.1f}s, dim={self._dim}")

        # Verify dimension by encoding a test string
        if is_m3:
            test_vec = self._model.encode(["test"], batch_size=1)["dense_vecs"]
        else:
            test_vec = self._model.encode(["test"])
        actual_dim = test_vec.shape[1] if hasattr(test_vec, 'shape') else len(test_vec[0])
        if actual_dim != self._dim:
            logger.warning(f"Dimension mismatch: expected {self._dim}, got {actual_dim}. Auto-correcting.")
            self._dim = actual_dim

        return self._model

    async def embed_texts(
        self,
        texts: list[str],
        *,
        return_sparse: bool = False,
    ) -> list[list[float]]:
        """Batch-embed texts into dense vectors."""
        if not texts:
            return []

        model = await self._ensure_model()
        start = time.time()
        batch_size = min(self.BATCH_SIZE, max(1, len(texts)))

        is_m3 = "m3" in self._model_name.lower()
        if is_m3:
            output = model.encode(
                texts,
                batch_size=batch_size,
                max_length=8192,
                return_dense=True,
                return_sparse=return_sparse,
                return_colbert_vecs=False,
            )
            dense = output["dense_vecs"]
        else:
            dense = model.encode(texts, batch_size=batch_size)

        if isinstance(dense, np.ndarray):
            dense = dense.tolist()

        elapsed = (time.time() - start) * 1000
        logger.debug(f"Embedded {len(texts)} texts in {elapsed:.0f}ms "
                     f"({elapsed/len(texts):.1f}ms/text)")

        return dense

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        results = await self.embed_texts([query])
        return results[0]

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def is_ready(self) -> bool:
        return self._model is not None


embedding_engine = EmbeddingEngine()
