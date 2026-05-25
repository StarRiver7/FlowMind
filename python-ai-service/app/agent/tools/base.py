# ============================================================
# agent/tools/base.py — Tool Layer Abstract
# ============================================================
"""Tool Layer — defines the contract for agent-invokable tools.

Tools are external functions that the agent can call to:
    - Perform calculations
    - Search the web
    - Query databases
    - Call external APIs
    - Execute custom business logic

Provides:
    - ToolDefinition: OpenAPI-compatible function schema
    - ToolResult: structured execution result
    - BaseTool: abstract tool contract
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ToolDefinition:
    """OpenAI-compatible function definition for tool calling."""
    name: str
    description: str
    parameters: dict  # JSON Schema
    require_confirm: bool = False
    timeout_seconds: int = 30
    category: str = "general"


@dataclass
class ToolResult:
    """Structured result from tool execution."""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: int = 0


class BaseTool(ABC):
    """Abstract contract for agent-invokable tools.

    Each tool provides:
        - definition: schema for LLM function calling
        - execute: the actual implementation
        - (optional) confirm: pre-execution user confirmation
    """

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the tool's function definition schema."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with provided arguments.

        Args:
            **kwargs: Arguments matching the definition.parameters schema

        Returns:
            String result (may be JSON-serializable for structured output)
        """
        ...

    @property
    def require_confirm(self) -> bool:
        """Whether this tool requires user confirmation before execution."""
        return self.definition.require_confirm

    @property
    def timeout(self) -> int:
        """Execution timeout in seconds."""
        return self.definition.timeout_seconds
