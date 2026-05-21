from typing import Any
from src.tools.base import BaseTool, ToolDefinition
from src.tools.executor import tool_executor
from src.tools.builtin.calculator import CalculatorTool
from src.tools.builtin.web_search import WebSearchTool
from src.utils.exceptions import ToolException


class ToolRegistry:
    """工具注册中心 — 管理所有可用工具"""

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
            {
                "type": "function",
                "function": {
                    "name": t.definition.name,
                    "description": t.definition.description,
                    "parameters": t.definition.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": t.definition.name,
                "description": t.definition.description,
                "require_confirm": t.require_confirm,
                "timeout": t.timeout,
            }
            for t in self._tools.values()
        ]

    async def execute(
        self,
        name: str,
        user_id: int | None = None,
        conversation_id: int | None = None,
        **kwargs,
    ) -> dict:
        """执行工具调用 — 含超时、校验、日志记录"""
        tool = self.get(name)

        exec_result = await tool_executor.execute(
            tool_name=name,
            tool_callable=tool.execute,
            require_confirm=tool.require_confirm,
            timeout=tool.timeout,
            **kwargs,
        )

        # 异步写日志到DB（不阻塞主流程）
        try:
            from src.services.tool_log_service import tool_log_service
            await tool_log_service.log(
                tool_name=name,
                tool_params=kwargs,
                tool_result=exec_result.get("result"),
                status=1 if exec_result["success"] else 0,
                error_msg=exec_result.get("error"),
                execution_time_ms=exec_result.get("execution_time_ms", 0),
                user_id=user_id,
                conversation_id=conversation_id,
            )
        except Exception:
            pass

        if not exec_result["success"]:
            raise ToolException(exec_result.get("error", "Tool execution failed"))

        return exec_result


tool_registry = ToolRegistry()
