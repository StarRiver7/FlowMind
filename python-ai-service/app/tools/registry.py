import time
import asyncio
import json
from typing import Any
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from app.core.config import settings
from app.common.exceptions.exceptions import ToolException


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict = Field(default_factory=dict)  # JSON Schema
    require_confirm: bool = False
    timeout: int = 30


class BaseTool(ABC):
    """工具抽象基类 - 所有工具必须实现"""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        pass


class CalculatorTool(BaseTool):
    """安全计算器 - 使用受限表达式求值"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calculator",
            description="Evaluate a mathematical expression with +, -, *, /, **, sqrt, sin, cos, log, abs, pi, e",
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "Math expression"}},
                "required": ["expression"],
            },
            timeout=10,
        )

    async def execute(self, expression: str = "") -> str:
        try:
            import numexpr
            result = numexpr.evaluate(expression).item()
            if isinstance(result, float):
                return f"{result:.6f}".rstrip("0").rstrip(".")
            return str(result)
        except ImportError:
            import math
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
            allowed_names["__builtins__"] = {}
            import re
            if not re.match(r'^[\d\s+\-*/().,%^eEpPiIsSiInNcCoOsStTaAnNqQlLgGrR]+$', expression):
                return "Error: disallowed characters in expression"
            try:
                result = eval(expression, {"__builtins__": {}}, allowed_names)
            except Exception:
                result = eval(expression, {"__builtins__": {}}, {})
            return str(result)


class WebSearchTool(BaseTool):
    """网页搜索工具"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_search",
            description="Search the web for real-time information",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"],
            },
            timeout=30,
        )

    async def execute(self, query: str = "") -> str:
        try:
            from langchain_community.tools import DuckDuckGoSearchResults
            tool = DuckDuckGoSearchResults(max_results=5)
            result = await tool.arun(query)
            return result
        except ImportError:
            return f"[WebSearch stub] Results for: {query} (install langchain-community for real search)"


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._register_builtins()

    def _register_builtins(self):
        self.register(CalculatorTool())
        self.register(WebSearchTool())

    def register(self, tool: BaseTool):
        self._tools[tool.definition.name] = tool

    def get(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolException(f"Tool not found: {name}")
        return tool

    def get_all_definitions(self) -> list[dict]:
        return [
            {"type": "function", "function": {
                "name": t.definition.name,
                "description": t.definition.description,
                "parameters": t.definition.parameters,
            }}
            for t in self._tools.values()
        ]

    def list_tools(self) -> list[dict]:
        return [
            {"name": t.definition.name, "description": t.definition.description,
             "require_confirm": t.definition.require_confirm, "timeout": t.definition.timeout}
            for t in self._tools.values()
        ]

    async def execute(self, name: str, **kwargs) -> dict:
        tool = self.get(name)
        timeout = tool.definition.timeout or settings.tool_timeout_seconds
        start = time.time()

        try:
            result = await asyncio.wait_for(tool.execute(**kwargs), timeout=timeout)
            elapsed_ms = int((time.time() - start) * 1000)
            return {"success": True, "result": result, "execution_time_ms": elapsed_ms}
        except asyncio.TimeoutError:
            elapsed_ms = int((time.time() - start) * 1000)
            return {"success": False, "error": f"Tool '{name}' timed out after {timeout}s", "execution_time_ms": elapsed_ms}
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            return {"success": False, "error": str(e), "execution_time_ms": elapsed_ms}


tool_registry = ToolRegistry()
