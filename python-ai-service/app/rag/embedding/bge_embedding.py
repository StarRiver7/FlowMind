"""BGE-M3 Embedding — InternSU BGE model wrapper.

Wraps the existing app.pipeline.embedder.EmbeddingEngine with:
  - BGE-M3 dense embeddings (1024-dim)
  - Long text support (8192 tokens)
  - GPU acceleration with FP16 (auto-detect)
  - Normalized output vectors
"""

from app.pipeline.embedder import embedding_engine
from app.core.logger import get_logger

logger = get_logger(__name__)


class BgeEmbedding:
    """BGE-M3 embedding provider.

    Thin wrapper around the existing EmbeddingEngine,
    adding InternSU features: health checks, dimension info, batch sizing.
    """

    def __init__(self):
        self._engine = embedding_engine

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed texts into 1024-dim dense vectors."""
        return await self._engine.embed_texts(texts)

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        return await self._engine.embed_query(query)

    @property
    def dim(self) -> int:
        return self._engine.dim

    @property
    def model_name(self) -> str:
        from app.core.config import settings
        return settings.bge_model_name

    @property
    def is_ready(self) -> bool:
        return self._engine.is_ready

    async def ensure_ready(self):
        """Warm up the model — call before first use."""
        await self._engine._ensure_model()
        logger.info(f"[BgeEmbedding] Model ready: {self.model_name} dim={self.dim}")


bge_embedding = BgeEmbedding()
