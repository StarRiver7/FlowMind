
"""InternSU LangGraph 统一 State 定义。

贯穿整个 Graph 工作流的共享状态，所有节点读写此对象。

用户指定字段:
  conversation_id, user_id, user_message, intent,
  clarify_required, clarify_question, conversation_context,
  trace_steps, final_answer, current_node
"""

from typing import TypedDict, Annotated, Optional, Any
from operator import add


class InternState(TypedDict):
    """InternSU LangGraph 全局状态。

    数据流: START -> intent_node -> clarify_node -> router_node -> chat_node -> response_node -> END
    """

    # ---- 基础标识 ----
    conversation_id: str                     # 会话 ID
    user_id: str                             # 用户 ID

    # ---- 输入 ----
    user_message: str                        # 用户原始消息
    conversation_context: Annotated[list[dict], add]  # 对话历史 (累积)

    # ---- 意图识别 ----
    intent: str                              # chat / clarify / rag / sql / summarize / unclear
    intent_confidence: float                 # 意图置信度 0.0~1.0

    # ---- Clarify 反问 ----
    clarify_required: bool                   # 是否需要反问澄清
    clarify_question: str                    # AI 反问的问题文本
    clarify_round: int                       # 当前反问轮次 (从1开始)
    clarify_pending: bool                    # 是否有待用户回答的反问
    collected_slots: dict                    # 已收集的参数槽位 {time_range: 本月, department: 技术部}

    # ---- 路由 ----
    current_node: str                        # 当前所在节点名
    next_node: str                           # 下一个节点名

    # ---- 工作过程追踪 ----
    trace_steps: Annotated[list[dict], add]  # 工作步骤记录

    # ---- 回答生成 ----
    system_prompt: str                       # 注入的 System Prompt
    final_answer: str                        # 最终回答文本
    tokens_used: int                         # Token 消耗
    model_name: str                          # 使用的模型名

    # ---- 元数据 ----
    error: Optional[str]                     # 错误信息
    done: bool                               # 是否完成


def create_initial_state(
    user_id: str,
    conversation_id: str,
    message: str,
    history: list[dict] | None = None,
    model_name: str = "deepseek-chat",
) -> InternState:
    """创建 Graph 初始状态。

    Args:
        user_id: 用户 ID
        conversation_id: 会话 ID
        message: 用户输入的消息文本
        history: 历史对话上下文
        model_name: LLM 模型名
    """
    return InternState(
        conversation_id=conversation_id,
        user_id=user_id,
        user_message=message,
        conversation_context=history or [],
        intent="chat",
        intent_confidence=0.0,
        clarify_required=False,
        clarify_question="",
        clarify_round=0,
        clarify_pending=False,
        collected_slots={},
        current_node="",
        next_node="",
        sources=[],
        trace_steps=[],
        system_prompt="",
        final_answer="",
        tokens_used=0,
        model_name=model_name,
        error=None,
        done=False,
    )
