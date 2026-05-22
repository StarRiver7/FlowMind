from typing import Any
from app.core.config import settings


class EmbedderService:
    """Embedding服务 — 文本向量化，后续接入Milvus时替换为BGE-M3本地模型"""

    def __init__(self):
        self._model_name = settings.embedding_model
        self._dim = settings.embedding_dim

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化 — 当前为降级实现，生产环境接入BGE-M3"""
        from app.llm.model_factory import llm_gateway
        return await llm_gateway.embed(texts)

    async def embed_query(self, query: str) -> list[float]:
        """单个查询向量化"""
        results = await self.embed_texts([query])
        return results[0]

    @property
    def dim(self) -> int:
        return self._dim


embedder_service = EmbedderService()
