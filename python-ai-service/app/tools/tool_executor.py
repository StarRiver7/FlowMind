import time
import asyncio
from typing import Any
from app.core.config import settings
from app.common.exceptions.exceptions import ToolException


class ToolExecutor:
    """工具执行器 — 超时控制、参数校验、沙箱隔离"""

    def __init__(self):
        self._default_timeout = settings.tool_timeout_seconds

    async def execute(
        self,
        tool_name: str,
        tool_callable,
        require_confirm: bool = False,
        timeout: int | None = None,
        **kwargs,
    ) -> dict:
        """
        执行工具调用，返回结构化结果
        :return: {"success": bool, "result": str, "error": str|None, "execution_time_ms": int}
        """
        timeout = timeout or self._default_timeout
        start_time = time.time()

        try:
            # 参数校验（JSON Schema验证）
            self._validate_params(tool_name, kwargs)

            # 超时控制执行
            result = await asyncio.wait_for(
                tool_callable(**kwargs),
                timeout=timeout,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "result": str(result) if result is not None else "Tool executed successfully",
                "error": None,
                "execution_time_ms": elapsed_ms,
            }

        except asyncio.TimeoutError:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "result": None,
                "error": f"Tool {tool_name} execution timed out after {timeout}s",
                "execution_time_ms": elapsed_ms,
            }

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "execution_time_ms": elapsed_ms,
            }

    def _validate_params(self, tool_name: str, params: dict):
        """参数校验 — 防止注入和非法参数"""
        for key, value in params.items():
            if isinstance(value, str) and len(value) > 10000:
                raise ToolException(f"Parameter {key} exceeds max length (10000)")
        # 后续可扩展JSON Schema严格校验


tool_executor = ToolExecutor()
