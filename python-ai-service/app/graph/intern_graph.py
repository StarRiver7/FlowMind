
"""InternSU LangGraph 主流程。

完整 AI 链路:
  START
    |
    v
  intent_node (意图识别)
    |
    +-- clarify  --> clarify_node --> END (反问后等待用户回答)
    +-- rag      --> rag_node      --> answer_node --> END
    +-- sql      --> sql_node      --> answer_node --> END
    +-- chat     --> answer_node   --> END

每一步通过 traces 记录工作过程，供前端"实习生工作过程"面板展示。
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from app.graph.state import InternState, create_initial_state
from app.graph.nodes.intent_node import intent_node
from app.graph.nodes.clarify_node import clarify_node
from app.graph.nodes.rag_node import rag_node
from app.graph.nodes.sql_node import sql_node
from app.graph.nodes.answer_node import answer_node

from app.core.logger import get_logger

logger = get_logger(__name__)


def route_after_intent(state: InternState) -> Literal["clarify_node", "rag_node", "sql_node", "answer_node"]:
    """意图路由: 根据 intent 决定下一步。"""
    intent = state.get("intent", "chat")
    route_map = {
        "clarify": "clarify_node",
        "rag": "rag_node",
        "sql": "sql_node",
        "chat": "answer_node",
    }
    target = route_map.get(intent, "answer_node")
    logger.debug(f"Routing: intent={intent} -> {target}")
    return target


def build_intern_graph() -> StateGraph:
    """构建 InternSU LangGraph StateGraph。"""
    graph = StateGraph(InternState)

    # 注册节点
    graph.add_node("intent_node", intent_node)
    graph.add_node("clarify_node", clarify_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("sql_node", sql_node)
    graph.add_node("answer_node", answer_node)

    # 入口
    graph.set_entry_point("intent_node")

    # 意图路由
    graph.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {
            "clarify_node": "clarify_node",
            "rag_node": "rag_node",
            "sql_node": "sql_node",
            "answer_node": "answer_node",
        },
    )

    # 各节点 -> 最终回答 或 结束
    graph.add_edge("rag_node", "answer_node")
    graph.add_edge("sql_node", "answer_node")

    # 回答节点和反问节点直接结束
    graph.add_edge("answer_node", END)
    graph.add_edge("clarify_node", END)

    return graph.compile()


class InternGraph:
    """InternSU Graph 封装。

    提供统一的异步调用接口，封装 LangGraph 的 ainvoke。
    """

    def __init__(self):
        self._graph = build_intern_graph()

    async def run(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        history: list[dict] | None = None,
        permission_context: dict | None = None,
        model_name: str = "deepseek-chat",
    ) -> InternState:
        """执行完整的 AI 处理流程。

        Args:
            user_id: 用户 ID
            conversation_id: 会话 ID
            message: 用户消息
            history: 历史对话
            permission_context: 权限上下文
            model_name: 模型名

        Returns:
            完整的 InternState，包含 final_response、traces、sources 等
        """
        state = create_initial_state(
            user_id=user_id,
            conversation_id=conversation_id,
            message=message,
            history=history,
            permission_context=permission_context,
            model_name=model_name,
        )

        result = await self._graph.ainvoke(state)
        logger.info(
            f"Graph completed: intent={result.get('intent')}, "
            f"traces={len(result.get('traces', []))}, "
            f"sources={len(result.get('sources', []))}"
        )
        return result

    @property
    def graph(self):
        return self._graph


# 全局单例
intern_graph = InternGraph()
