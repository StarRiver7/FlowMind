from enum import Enum
from typing import TypedDict, Annotated, Optional
from operator import add


class IntentType(str, Enum):
    CHAT = "chat"
    RAG = "rag"
    TOOL = "tool"
    SQL = "sql"


class RouterState(TypedDict):
    user_id: str
    conversation_id: str
    message: str
    history: Annotated[list[dict], add]
    intent: str
    retrieved_docs: Annotated[list[dict], add]
    tool_results: Annotated[list[dict], add]
    llm_response: str
    final_response: str
    error: Optional[str]
    done: bool


SYSTEM_PROMPTS = {
    IntentType.CHAT: (
        "You are FlowMind, an enterprise AI assistant. "
        "Be helpful, concise, and professional. "
        "Answer the user's question directly."
    ),
    IntentType.RAG: (
        "You are FlowMind, an enterprise knowledge assistant. "
        "Answer based on the retrieved context documents. "
        "If context is insufficient, say so. Cite document sources."
    ),
    IntentType.TOOL: (
        "You are FlowMind, an enterprise AI assistant with tool access. "
        "Use available tools to help the user. "
        "Explain what tool you are using and why."
    ),
    IntentType.SQL: (
        "You are a SQL query assistant. Generate valid SELECT queries. "
        "Only SELECT, always LIMIT, use table aliases."
    ),
}
