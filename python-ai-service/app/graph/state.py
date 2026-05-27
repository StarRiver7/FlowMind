from typing import TypedDict, Annotated, Optional
from operator import add

class InternState(TypedDict):
    conversation_id: str
    user_id: str
    user_message: str
    conversation_context: Annotated[list[dict], add]
    intent: str
    intent_confidence: float
    clarify_required: bool
    clarify_question: str
    clarify_round: int
    clarify_pending: bool
    collected_slots: dict
    clarify_slots: dict
    missing_slots: list[str]
    clarify_finished: bool
    pending_task: str
    task_context: dict
    current_node: str
    next_node: str
    sources: list[dict]
    trace_steps: list[dict]
    system_prompt: str
    final_answer: str
    tokens_used: int
    model_name: str
    error: Optional[str]
    done: bool

def create_initial_state(user_id, conversation_id, message, history=None, model_name=None, restore_state=None):
    if model_name is None: model_name = "deepseek-chat"
    if restore_state is None: restore_state = {}
    rs = restore_state
    return InternState(
        conversation_id=conversation_id, user_id=user_id, user_message=message,
        conversation_context=history or [],
        intent=rs.get("intent", "chat"),
        intent_confidence=rs.get("intent_confidence", 0.0),
        clarify_required=rs.get("clarify_required", False),
        clarify_question=rs.get("clarify_question", ""),
        clarify_round=rs.get("clarify_round", 0),
        clarify_pending=rs.get("clarify_pending", False),
        collected_slots=rs.get("collected_slots", {}),
        clarify_slots=rs.get("clarify_slots", {}),
        missing_slots=rs.get("missing_slots", []),
        clarify_finished=rs.get("clarify_finished", False),
        pending_task=rs.get("pending_task", ""),
        task_context=rs.get("task_context", {}),
        current_node="", next_node="",
        sources=[], trace_steps=[],
        system_prompt="", final_answer="", tokens_used=0,
        model_name=model_name, error=None, done=False,
    )
