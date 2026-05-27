
"""InternSU LangGraph 主流程引擎。

纯 Graph 链路 (Phase 1):
  START
    |
    v
  intent_node    — 意图识别 + 澄清判定
    |
    +-- clarify_required=True  → clarify_node → router_node
    +-- clarify_required=False → router_node
    |
    v
  router_node    — 根据 intent 路由分发
    |
    v
  chat_node      — LLM 对话生成
    |
    v
  response_node  — 统一输出汇总
    |
    v
  END

Phase 2 扩展: 在 router_node 后增加 rag_node / sql_node 分支。
"""

from langgraph.graph import StateGraph, END

from app.graph.state import InternState, create_initial_state
from app.graph.nodes.intent_node import intent_node
from app.graph.nodes.clarify_node import clarify_node
from app.graph.nodes.router_node import router_node
from app.graph.nodes.chat_node import chat_node
from app.graph.nodes.response_node import response_node

from app.graph.edges.routes import (
    route_after_intent,
    route_after_clarify,
    route_after_router,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


def build_intern_graph() -> StateGraph:
    """构建 InternSU LangGraph。

    Returns:
        已编译的 StateGraph，可直接调用 ainvoke()。
    """
    graph = StateGraph(InternState)

    # ---- 注册节点 ----
    graph.add_node("intent_node", intent_node)
    graph.add_node("clarify_node", clarify_node)
    graph.add_node("router_node", router_node)
    graph.add_node("chat_node", chat_node)
    graph.add_node("response_node", response_node)

    # ---- 入口 ----
    graph.set_entry_point("intent_node")

    # ---- 边 ----
    # intent_node → clarify_node (需要反问) 或 router_node (直接路由)
    graph.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {"clarify_node": "clarify_node", "router_node": "router_node"},
    )

    # clarify_node → router_node (继续分发)
    graph.add_edge("clarify_node", "router_node")

    # router_node → chat_node (Phase 2: 扩展 rag/sql 分支)
    graph.add_conditional_edges(
        "router_node",
        route_after_router,
        {"chat_node": "chat_node"},
    )

    # chat_node → response_node → END
    graph.add_edge("chat_node", "response_node")
    graph.add_edge("response_node", END)

    return graph.compile()


class InternGraph:
    """InternSU Graph 封装。

    对外提供统一的异步调用接口。
    """

    def __init__(self):
        self._graph = build_intern_graph()

    async def run(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        history: list[dict] | None = None,
        model_name: str = "deepseek-chat",
    ) -> InternState:
        """执行完整 Graph 链路。

        Args:
            user_id: 用户 ID
            conversation_id: 会话 ID
            message: 用户输入
            history: 历史对话上下文
            model_name: LLM 模型名

        Returns:
            完成后的 InternState，包含 final_answer 和 trace_steps
        """
        state = create_initial_state(
            user_id=user_id,
            conversation_id=conversation_id,
            message=message,
            history=history,
            model_name=model_name,
        )

        result = await self._graph.ainvoke(state)

        logger.info(
            f"Graph completed: {len(result.get('trace_steps', []))} steps, "
            f"intent={result.get('intent')}, "
            f"answer_len={len(result.get('final_answer', ''))}"
        )
        return result

    @property
    def graph(self):
        return self._graph


# 全局单例
intern_graph = InternGraph()
