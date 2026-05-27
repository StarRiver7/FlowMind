
"""Response 统一输出节点。

职责:
  汇总 trace_steps、final_answer 等输出信息。
  为 SSE 推送提供统一的最终状态快照。
"""

import time
from app.graph.state import InternState
from app.core.logger import get_logger

logger = get_logger(__name__)


async def response_node(state: InternState) -> InternState:
    """统一响应节点。

    汇总元数据，标记最终完成状态。
    SSE handler 读取此 state 生成事件流。
    """
    t0 = time.time()
    state["current_node"] = "response_node"

    state["trace_steps"] = state.get("trace_steps", []) + [{
        "node": "response_node",
        "message": "正在准备输出...",
        "status": "completed",
        "detail": {
            "total_tokens": state.get("tokens_used", 0),
            "intent": state.get("intent", "chat"),
            "trace_count": len(state.get("trace_steps", [])),
            "clarify_pending": state.get("clarify_pending", False),
        },
        "duration_ms": int((time.time() - t0) * 1000),
        "timestamp": _now(),
    }]

    state["done"] = True
    logger.info(
        f"ResponseNode: intent={state.get('intent')}, "
        f"answer_len={len(state.get('final_answer', ''))}, "
        f"traces={len(state.get('trace_steps', []))}"
    )
    return state


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
