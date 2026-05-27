
"""Graph 边路由逻辑。

所有条件路由集中管理，决策依据为 InternState 的状态字段。
"""

from typing import Literal
from app.graph.state import InternState
from app.core.logger import get_logger

logger = get_logger(__name__)


def route_after_intent(state: InternState) -> Literal["clarify_node", "router_node"]:
    """意图识别后的路由。

    如果意图识别判定需要澄清 (clarify_required=True) -> 进入 clarify_node
    否则 -> 进入 router_node 继续分发
    """
    if state.get("clarify_required", False):
        logger.info(f"Route: intent_node -> clarify_node (reason: info insufficient)")
        return "clarify_node"
    logger.info(f"Route: intent_node -> router_node (intent={state.get('intent', 'chat')})")
    return "router_node"


def route_after_clarify(state: InternState) -> Literal["router_node"]:
    """反问澄清后的路由。

    clarify 完成后总是进入 router 重新分发。
    此时 clarify_pending = True, 等待用户下一轮回答后重新进入 Graph。
    """
    logger.info("Route: clarify_node -> router_node")
    return "router_node"


def route_after_router(state: InternState) -> Literal["chat_node"]:
    """路由节点后的分发。

    根据 intent 分发到对应处理器:
      chat       -> chat_node
      rag        -> chat_node (Phase 2: 改为 rag_node)
      sql        -> chat_node (Phase 2: 改为 sql_node)
      summarize  -> chat_node (Phase 2: 改为 summarize_node)
      unclear    -> chat_node (直接回应)

    Phase 2 扩展: 在此处增加 rag_node / sql_node 的路由分支。
    """
    intent = state.get("intent", "chat")

    # Phase 2 预留扩展点:
    # if intent == "rag":
    #     return "rag_node"
    # if intent == "sql":
    #     return "sql_node"

    logger.info(f"Route: router_node -> chat_node (intent={intent})")
    return "chat_node"
