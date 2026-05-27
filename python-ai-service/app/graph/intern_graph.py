from langgraph.graph import StateGraph, END
from app.graph.state import InternState, create_initial_state
from app.graph.nodes.intent_node import intent_node
from app.graph.nodes.clarify_node import clarify_node
from app.graph.nodes.slot_collect_node import slot_collect_node
from app.graph.nodes.task_resume_node import task_resume_node
from app.graph.nodes.router_node import router_node
from app.graph.nodes.chat_node import chat_node
from app.graph.nodes.sql_node import sql_node
from app.graph.nodes.rag_retrieval_node import rag_retrieval_node
from app.graph.nodes.response_node import response_node
from app.graph.edges.routes import route_after_intent, route_after_slot_collect, route_after_router
from app.core.logger import get_logger
logger = get_logger(__name__)

def build_intern_graph():
    graph = StateGraph(InternState)
    graph.add_node("intent_node", intent_node)
    graph.add_node("clarify_node", clarify_node)
    graph.add_node("slot_collect_node", slot_collect_node)
    graph.add_node("task_resume_node", task_resume_node)
    graph.add_node("router_node", router_node)
    graph.add_node("chat_node", chat_node)
    graph.add_node("sql_node", sql_node)
    graph.add_node("rag_retrieval_node", rag_retrieval_node)
    graph.add_node("response_node", response_node)
    graph.set_entry_point("intent_node")
    graph.add_conditional_edges("intent_node", route_after_intent, {"clarify_node": "clarify_node", "slot_collect_node": "slot_collect_node", "router_node": "router_node"})
    graph.add_conditional_edges("slot_collect_node", route_after_slot_collect, {"clarify_node": "clarify_node", "task_resume_node": "task_resume_node"})
    graph.add_edge("clarify_node", END)
    graph.add_edge("task_resume_node", "router_node")
    graph.add_conditional_edges("router_node", route_after_router, {"chat_node": "chat_node", "sql_node": "sql_node", "rag_retrieval_node": "rag_retrieval_node"})
    graph.add_edge("chat_node", "response_node")
    graph.add_edge("sql_node", "response_node")
    graph.add_edge("rag_retrieval_node", "response_node")
    graph.add_edge("response_node", END)
    return graph.compile()

class InternGraph:
    def __init__(self):
        self._graph = build_intern_graph()
    async def run(self, user_id, conversation_id, message, history=None, model_name="deepseek-chat", restore_state=None):
        state = create_initial_state(user_id=user_id, conversation_id=conversation_id, message=message, history=history, model_name=model_name, restore_state=restore_state)
        logger.info(f"Graph START: msg={message[:30]}, restore_clarify={restore_state.get("clarify_pending") if restore_state else False}")
        result = await self._graph.ainvoke(state)
        logger.info(f"Graph END: intent={result.get("intent")}, clarify_pending={result.get("clarify_pending")}, final_answer_len={len(result.get("final_answer", ""))}, traces={len(result.get("trace_steps", []))}")
        logger.info(f"Graph done: {len(result.get("trace_steps", []))} steps")
        return result
    @property
    def graph(self):
        return self._graph

intern_graph = InternGraph()
