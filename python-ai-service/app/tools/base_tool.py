from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """工具元数据定义（给LLM看的function calling描述）"""
    name: str
    description: str
    parameters: dict  # JSON Schema


class BaseTool(ABC):
    """工具抽象基类"""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        pass

    @property
    def require_confirm(self) -> bool:
        return False

    @property
    def timeout(self) -> int:
        return 30
