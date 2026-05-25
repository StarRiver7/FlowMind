"""
LangGraph Router — intent classification + RAG + Tool orchestration.

Uses LangGraph StateGraph for flexible routing:
    classify_intent -> {rag_node, tool_node, chat_node} -> final_response
"""
import json
import re
from typing import Literal
from langgraph.graph import StateGraph, END
from app.router.models import RouterState, IntentType
from app.llm.gateway import llm_gateway
from app.prompt.manager import prompt_manager
from app.pipeline.rag_pipeline import rag_pipeline
from app.tools.registry import tool_registry
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


async def classify_intent(state: RouterState) -> RouterState:
    """LLM semantic intent classification node."""
    msg = state["message"]
    messages = [
        {"role": "system", "content": (
            "Classify the user message into exactly one intent category. "
            "Respond with ONLY the category name: chat, rag, tool, or sql.\n"
            "- chat: casual conversation, general questions, greetings\n"
            "- rag: knowledge/document lookup, policy questions, how-to\n"
            "- tool: calculation, search, external action needed\n"
            "- sql: data queries, statistics, reporting, rankings"
        )},
        {"role": "user", "content": msg},
    ]
    try:
        resp = await llm_gateway.chat(messages, temperature=0.0, max_tokens=10)
        intent_str = resp.content.strip().lower()
        if intent_str not in ("chat", "rag", "tool", "sql"):
            intent_str = "chat"
        state["intent"] = intent_str
        logger.debug(f"Intent classified: {intent_str} for '{msg[:50]}...'")
    except Exception as e:
        logger.warning(f"Intent classification failed, fallback to chat: {e}")
        state["intent"] = "chat"
    return state


async def rag_node(state: RouterState) -> RouterState:
    """RAG retrieval node — hybrid search with reranking."""
    try:
        docs = await rag_pipeline.search(
            query=state["message"],
            top_k=settings.rag_final_k,
            use_rerank=True,
            with_citation=True,
            tenant_id="default",
        )
        state["retrieved_docs"] = docs
        logger.debug(f"RAG retrieved {len(docs)} docs")
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        state["retrieved_docs"] = []
    return state


async def tool_node(state: RouterState) -> RouterState:
    """Tool execution node."""
    try:
        messages = [
            {"role": "system", "content": (
                "Call the appropriate tool based on the user's request. "
                'Respond in JSON: {"tool": "name", "params": {...}}'
            )},
            {"role": "user", "content": state["message"]},
        ]
        resp = await llm_gateway.chat(messages, temperature=0.0, max_tokens=256)

        json_match = re.search(r'\{[\s\S]*"tool"[\s\S]*\}', resp.content)
        if json_match:
            tool_call = json.loads(json_match.group())
            result = await tool_registry.execute(tool_call["tool"], **tool_call.get("params", {}))
            state["tool_results"] = [result]
            logger.info(f"Tool '{tool_call['tool']}' executed: success={result['success']}")
        else:
            state["tool_results"] = [{"success": False, "error": "Could not parse tool call"}]
    except Exception as e:
        logger.warning(f"Tool execution failed: {e}")
        state["tool_results"] = [{"success": False, "error": str(e)}]
    return state


async def chat_node(state: RouterState) -> RouterState:
    """Final response generation node."""
    intent = state.get("intent", "chat")
    history = state.get("history", [])
    message = state["message"]

    if intent == "rag" and state.get("retrieved_docs"):
        docs = state["retrieved_docs"]
        context_str = "\n\n".join(
            f"[Source: {d.get('metadata', {}).get('file_name', 'doc')}] {d['content']}"
            for d in docs
        )
        messages = [
            {"role": "system", "content": (
                f"Answer based on the following context:\n\n{context_str}\n\n"
                "Be concise and cite sources."
            )},
        ]
        if history:
            messages.extend(history[-settings.conversation_window * 2:])
        messages.append({"role": "user", "content": message})
    elif intent == "tool" and state.get("tool_results"):
        tool_output = "\n".join(
            r.get("result", r.get("error", ""))
            for r in state["tool_results"]
        )
        messages = [
            {"role": "system", "content": f"Tool results:\n{tool_output}\n\nSummarize for the user."},
            {"role": "user", "content": message},
        ]
    else:
        messages = prompt_manager.build_messages(
            "default-system", message, history=history,
        )

    try:
        resp = await llm_gateway.chat(messages)
        state["llm_response"] = resp.content
        state["final_response"] = resp.content
    except Exception as e:
        state["error"] = str(e)
        state["final_response"] = f"Sorry, I encountered an error: {e}"

    state["done"] = True
    return state


def route_by_intent(state: RouterState) -> Literal["rag_node", "tool_node", "chat_node"]:
    intent = state.get("intent", "chat")
    if intent == "rag":
        return "rag_node"
    elif intent == "tool":
        return "tool_node"
    return "chat_node"


def build_router_graph() -> StateGraph:
    graph = StateGraph(RouterState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("rag_node", rag_node)
    graph.add_node("tool_node", tool_node)
    graph.add_node("chat_node", chat_node)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges("classify_intent", route_by_intent, {
        "rag_node": "rag_node",
        "tool_node": "tool_node",
        "chat_node": "chat_node",
    })

    graph.add_edge("rag_node", "chat_node")
    graph.add_edge("tool_node", "chat_node")
    graph.add_edge("chat_node", END)

    return graph.compile()


router_graph = build_router_graph()
