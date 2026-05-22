from pydantic import BaseModel, Field
from typing import Optional


class RagSearchRequest(BaseModel):
    """知识库检索请求"""
    query: str = Field(..., min_length=1, max_length=4096, description="检索查询")
    top_k: int = Field(default=5, ge=1, le=50, description="返回Top-K结果")
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="最小相关度阈值")


class RagChunk(BaseModel):
    """检索到的文档片段"""
    chunk_id: str
    file_id: int
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)


class RagSearchResponse(BaseModel):
    """检索结果"""
    chunks: list[RagChunk]
    total: int


class RagIndexRequest(BaseModel):
    """触发文档索引请求"""
    file_id: int = Field(..., description="文件ID")
    file_path: str = Field(..., description="文件在对象存储中的路径")
    file_type: str = Field(..., description="文件类型: pdf/docx/md/txt")
