# ============================================================
# agent/base.py — Agent Layer Abstract
# ============================================================
"""Agent Layer — defines the contract for AI agent execution.

The Agent Layer is the top-level orchestrator that:
    1. Receives user input
    2. Routes through a LangGraph StateGraph
    3. Executes nodes (classify, retrieve, tool, generate)
    4. Manages conversation state and memory
    5. Returns structured responses (sync or streaming)

Provides:
    - AgentState: typed graph state
    - AgentResponse: structured output
    - BaseAgent: abstract agent contract
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, AsyncIterator, TypedDict, Annotated
from operator import add


class AgentState(TypedDict, total=False):
    """LangGraph StateGraph state schema.

    Fields annotated with 'add' use reducer semantics — values are
    appended rather than replaced across node executions.
    """
    user_id: str
    conversation_id: str
    message: str
    history: Annotated[list[dict], add]
    intent: str
    retrieved_docs: Annotated[list[dict], add]
    tool_calls: Annotated[list[dict], add]
    tool_results: Annotated[list[dict], add]
    llm_response: str
    final_response: str
    error: Optional[str]
    done: bool


@dataclass
class AgentResponse:
    """Structured response from agent execution."""
    content: str
    conversation_id: str
    intent: str
    sources: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    token_usage: Optional[dict] = None


class BaseAgent(ABC):
    """Abstract contract for AI agent execution.

    Agents orchestrate the full pipeline:
        Input → Intent Classification → [RAG/Tool/Chat] → Response

    Implementations use LangGraph StateGraph for routing logic.
    """

    @abstractmethod
    async def execute(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        *,
        use_rag: bool = True,
        use_tools: bool = True,
        **kwargs: Any,
    ) -> AgentResponse:
        """Execute a complete agent run synchronously.

        Returns the full AgentResponse after graph completion.
        """
        ...

    @abstractmethod
    async def execute_stream(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        *,
        use_rag: bool = True,
        use_tools: bool = True,
        **kwargs: Any,
    ) -> AsyncIterator[dict]:
        """Execute agent with streaming output.

        Yields individual SSE events as the graph executes.
        Final event includes sources, intent, and token usage.
        """
        ...
