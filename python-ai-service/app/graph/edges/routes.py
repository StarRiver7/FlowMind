from typing import Literal
from app.graph.state import InternState
from app.core.logger import get_logger
logger = get_logger(__name__)

def route_after_intent(state: InternState) -> Literal["clarify_node", "slot_collect_node", "router_node"]:
    if state.get("clarify_pending"):
        return "slot_collect_node"
    if state.get("clarify_required"):
        return "clarify_node"
    return "router_node"

def route_after_slot_collect(state: InternState) -> Literal["clarify_node", "task_resume_node"]:
    if state.get("clarify_finished"):
        return "task_resume_node"
    return "clarify_node"

def route_after_router(state: InternState) -> Literal["chat_node", "sql_node"]:
    intent = state.get("intent", "chat")
    if intent == "sql":
        return "sql_node"
    return "chat_node"
