from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class ApiResponse(BaseModel):
    """Python AI Service 统一响应结构（对齐Java端的Result）"""
    code: int = 200
    message: str = "success"
    data: Any = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp() * 1000)
    trace_id: Optional[str] = None


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp() * 1000)
