"""Agent Executor — LangGraph router + real SSE streaming + dual-layer memory.

Orchestrates the full AI pipeline with true token-by-token streaming:
    1. Intent classification (fast, non-streaming)
    2. RAG retrieval or Tool execution (fast, non-streaming)
    3. LLM response generation (streaming token by token via DeepSeek)
    4. Source citation returned in final done event
    5. Messages persisted to Redis (hot) + MySQL (cold)
"""
from typing import AsyncIterator
from app.router.graph import router_graph, RouterState
from app.router.stream_graph import stream_orchestrator
from app.memory.memory_manager import memory_manager
from app.core.logger import get_logger

logger = get_logger(__name__)


class AgentExecutor:
    """Enterprise agent executor with streaming and dual-layer memory."""

    # ---- Non-streaming chat (uses existing LangGraph) ----

    async def chat(
        self, user_id: str, conversation_id: str,
        message: str, use_rag: bool = True, use_tools: bool = True,
    ) -> dict:
        """Non-streaming chat using compiled LangGraph."""
        history = await memory_manager.get_history(user_id, conversation_id)

        state: RouterState = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message": message,
            "history": history,
            "intent": "chat",
            "retrieved_docs": [],
            "tool_results": [],
            "llm_response": "",
            "final_response": "",
            "error": None,
            "done": False,
        }

        result = await router_graph.ainvoke(state)

        # Persist to Redis + MySQL
        await memory_manager.record_turn(
            user_id=user_id,
            conversation_id=conversation_id,
            user_msg=message,
            assistant_msg=result["final_response"],
            sources=[
                {
                    "file": d.get("metadata", {}).get("file_name", ""),
                    "score": d.get("rerank_score") or d.get("score", 0),
                    "excerpt": d.get("excerpt", d.get("content", "")[:200]),
                }
                for d in result.get("retrieved_docs", [])
            ] if result.get("retrieved_docs") else None,
            intent=result.get("intent", "chat"),
        )

        return {
            "content": result["final_response"],
            "conversation_id": conversation_id,
            "intent": result.get("intent", "chat"),
            "sources": [
                {
                    "file": d.get("metadata", {}).get("file_name", ""),
                    "score": d.get("rerank_score") or d.get("score", 0),
                    "excerpt": d.get("excerpt", d.get("content", "")[:200]),
                }
                for d in result.get("retrieved_docs", [])
            ] if result.get("retrieved_docs") else None,
        }

    # ---- True streaming chat ----

    async def chat_stream(
        self, user_id: str, conversation_id: str,
        message: str, use_rag: bool = True, use_tools: bool = True,
        model: str | None = None,
    ) -> AsyncIterator[dict]:
        """Real token-by-token streaming chat.

        Yields structured events:
            {"type": "thinking", "content": "..."}
            {"type": "token", "content": "H"}
            {"type": "token", "content": "el"}
            {"type": "token", "content": "lo"}
            {"type": "done", "intent": "chat", "sources": [...], "conversation_id": "..."}
        """
        history = await memory_manager.get_history(user_id, conversation_id)

        # Persist user message immediately
        await memory_manager.add_message(user_id, conversation_id, "user", message)
        memory_manager.persist_user_message(user_id, conversation_id, message)

        full_text = ""
        final_intent = "chat"
        final_sources = []

        try:
            async for event in stream_orchestrator.stream_chat(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                history=history,
                use_rag=use_rag,
                use_tools=use_tools,
                model=model,
            ):
                if event["type"] == "token":
                    full_text += event["content"]
                elif event["type"] == "done":
                    final_intent = event.get("intent", "chat")
                    final_sources = event.get("sources", [])
                    # Use full_text from done event if available
                    if event.get("full_text"):
                        full_text = event["full_text"]
                yield event

        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield {"type": "error", "content": str(e)}
            yield {
                "type": "done",
                "intent": "chat",
                "sources": [],
                "conversation_id": conversation_id,
                "error": str(e),
            }

        # Persist assistant response to Redis + MySQL
        if full_text:
            await memory_manager.add_message(user_id, conversation_id, "assistant", full_text)
            memory_manager.persist_assistant_message(
                user_id, conversation_id, full_text,
                sources=final_sources, intent=final_intent,
            )

    # ---- Conversation management ----

    async def start_conversation(self, user_id: str, title: str = "") -> str:
        """Start a new conversation, returns conversation_id."""
        return await memory_manager.start_conversation(user_id, title)

    def get_conversations(self, user_id: str) -> list[dict]:
        """List user's conversations from MySQL."""
        return memory_manager.get_user_conversations(user_id)

    def get_history(self, conversation_id: str, limit: int = 50) -> list[dict]:
        """Get full message history for a conversation from MySQL."""
        return memory_manager.get_message_history(conversation_id, limit)


agent_executor = AgentExecutor()