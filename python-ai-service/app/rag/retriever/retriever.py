from typing import Any
from app.core.config import settings
from app.common.exceptions.exceptions import RAGException


class RetrieverService:
    """检索服务 — 混合检索（向量 + 关键词），Milvus集成点"""

    def __init__(self):
        self._top_k = settings.rag_top_k
        self._score_threshold = settings.rag_score_threshold
        self._milvus_ready = False

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[dict]:
        """执行混合检索 — 当前为降级实现，生产环境接入Milvus"""
        # TODO: 接入Milvus进行向量+关键词混合检索
        # 当前返回空结果，由调用方处理降级逻辑
        return []

    async def index_document(self, file_id: int, chunks: list[str]) -> int:
        """索引文档 — 当前为降级实现"""
        # TODO: 接入Milvus进行向量索引
        return len(chunks)


retriever_service = RetrieverService()
