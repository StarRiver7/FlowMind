"""Knowledge Base request/response schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ============================================================
# Knowledge Space schemas
# ============================================================

class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识空间请求."""
    name: str = Field(..., min_length=1, max_length=128, description="空间名称")
    description: Optional[str] = Field(default=None, max_length=512, description="描述")
    visibility: Literal["private", "department", "public"] = Field(default="private", description="可见范围")
    department_id: Optional[int] = Field(default=None, description="归属部门ID (visibility=department时必填)")
    embedding_model: str = Field(default="BGE-M3", description="Embedding模型")
    chunk_size: int = Field(default=512, ge=128, le=4096, description="分块大小")
    chunk_overlap: int = Field(default=64, ge=0, le=512, description="分块重叠")


class KnowledgeBaseResponse(BaseModel):
    """知识空间响应."""
    id: int
    name: str
    description: Optional[str] = None
    visibility: str
    department_id: Optional[int] = None
    creator_id: int
    document_count: int = 0
    chunk_count: int = 0
    embedding_model: str = "BGE-M3"
    status: int = 1
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeBaseListResponse(BaseModel):
    """知识空间列表响应."""
    items: list[KnowledgeBaseResponse]
    total: int


# ============================================================
# Document schemas
# ============================================================

class DocumentResponse(BaseModel):
    """文档响应."""
    id: int
    space_id: int
    file_name: str
    file_size: int
    file_type: str
    file_path: str
    file_hash: Optional[str] = None
    processing_status: str
    chunk_count: int = 0
    token_count: int = 0
    error_msg: Optional[str] = None
    creator_id: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """文档列表响应."""
    items: list[DocumentResponse]
    total: int


class UploadResponse(BaseModel):
    """上传响应."""
    document_id: int
    file_name: str
    file_type: str
    file_size: int
    processing_status: str
    file_hash: str
    space_id: int
    upload_time: Optional[datetime] = None


class DocumentStatusResponse(BaseModel):
    """文档状态响应."""
    document_id: int
    processing_status: str
    chunk_count: int
    token_count: int
    error_msg: Optional[str] = None


# ============================================================
# Upload progress SSE event
# ============================================================

class UploadProgressEvent(BaseModel):
    """上传进度SSE事件."""
    event: Literal["progress", "done", "error"]
    step: str  # e.g. "uploading", "saving", "validating", "recording"
    detail: Optional[str] = None
    document_id: Optional[int] = None
    file_name: Optional[str] = None
