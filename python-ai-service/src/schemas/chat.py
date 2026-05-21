from pydantic import BaseModel, Field
from typing import Optional, Literal


class ChatRequest(BaseModel):
    """Java服务转发来的对话请求"""
    conversation_id: str = Field(..., description="对话ID")
    user_id: str = Field(..., description="用户ID")
    message: str = Field(..., min_length=1, max_length=32000, description="用户消息")
    model: Optional[str] = Field(default=None, description="模型名称，不传则用默认")
    stream: bool = Field(default=True, description="是否流式返回")
    use_rag: bool = Field(default=True, description="是否启用知识库检索")
    use_tools: bool = Field(default=True, description="是否允许工具调用")


class ChatMessage(BaseModel):
    """对话中的单条消息"""
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    metadata: Optional[dict] = None


class ChatStreamChunk(BaseModel):
    """SSE流式输出的单个chunk"""
    content: str
    done: bool = False
    conversation_id: Optional[str] = None
    metadata: Optional[dict] = None
