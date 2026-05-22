from pydantic import BaseModel, Field
from typing import Optional


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="工具名称")
    params: dict = Field(default_factory=dict, description="工具参数")
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None


class ToolExecuteResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: int


class ToolLogQuery(BaseModel):
    user_id: Optional[int] = None
    tool_name: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
