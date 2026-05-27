
"""Router 路由节点。

职责:
  根据 intent 决定下游节点。
  当前阶段: 所有意图均路由到 chat_node。
  Phase 2: 扩展 rag_node / sql_node 分支。
"""

import time
from app.graph.state import InternState
from app.core.logger import get_logger

logger = get_logger(__name__)


async def router_node(state: InternState) -> InternState:
    """路由分发节点。

    仅做路由决策和日志记录，不修改 state 的核心字段。
    实际路由由 edges/routes.py::route_after_router 完成。
    """
    t0 = time.time()
    state["current_node"] = "router_node"

    intent = state.get("intent", "chat")

    state["trace_steps"] = state.get("trace_steps", []) + [{
        "node": "router_node",
        "message": f"正在分配任务: {_intent_cn(intent)}",
        "status": "completed",
        "detail": {"intent": intent, "next": "chat_node"},
        "duration_ms": int((time.time() - t0) * 1000),
        "timestamp": _now(),
    }]

    logger.info(f"RouterNode: intent={intent} -> chat_node")
    return state


def _intent_cn(intent: str) -> str:
    return {"chat": "一般对话", "rag": "知识检索", "sql": "数据查询",
            "clarify": "需要确认", "unclear": "不明确"}.get(intent, intent)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
