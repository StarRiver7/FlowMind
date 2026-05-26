
"""InternSU LangGraph State 定义。

基于产品定义，扩展 RouterState 以支持:
  - Clarify 反问机制
  - SQL 生成与执行
  - 工作过程追踪 (traces)
  - Source 引用 (sources)
  - 权限上下文 (permission_context)
"""

from typing import TypedDict, Annotated, Optional, Any
from operator import add


class TraceStep(TypedDict, total=False):
    """工作过程中单个步骤的记录。"""
    step: str               # 步骤名: intent_recognition, knowledge_retrieval 等
    status: str             # running, completed, failed
    step_order: int         # 步骤序号
    detail: dict | None     # 步骤详情
    started_at: str | None  # ISO 时间
    completed_at: str | None
    duration_ms: int | None


class SourceRef(TypedDict, total=False):
    """RAG 引用来源。"""
    document_id: int
    document_name: str
    chunk_index: int
    page_number: int | None
    excerpt: str
    score: float


class ClarifyQuestion(TypedDict):
    """反问澄清中的单个问题。"""
    question: str           # 问题文本
    default: str | None     # 默认值
    options: list[str] | None  # 可选项


class InternState(TypedDict):
    """InternSU LangGraph 全局状态。

    贯穿整个 Agent 工作流的共享状态对象。
    """

    # ---- 基础上下文 ----
    user_id: str
    conversation_id: str
    message: str                         # 当前用户消息
    history: Annotated[list[dict], add]  # 对话历史 (累积)

    # ---- 权限上下文 ----
    permission_context: dict             # {user_id, department_id, department_path, allowed_space_ids}

    # ---- 意图与路由 ----
    intent: str                          # chat, rag, sql, clarify
    intent_confidence: float             # 意图置信度

    # ---- Clarify 反问 ----
    clarify_questions: Annotated[list[dict], add]  # 反问问题列表
    clarify_round: int                   # 当前反问轮次
    pending_clarify: bool                # 是否有待确认的反问

    # ---- RAG 检索 ----
    retrieved_docs: Annotated[list[dict], add]  # 检索到的文档 chunk
    filtered_docs: list[dict]            # 权限过滤后的文档
    rag_context: str                     # 注入 LLM 的 RAG 上下文文本

    # ---- SQL Agent ----
    generated_sql: str                   # LLM 生成的 SQL
    sql_security_passed: bool            # 安全检查是否通过
    sql_security_detail: dict            # 安全检查详情
    executed_sql: str                    # 实际执行的 SQL
    sql_result: Any                      # SQL 执行结果
    sql_error: str | None                # SQL 执行错误

    # ---- 工作过程追踪 ----
    traces: Annotated[list[dict], add]   # 工作步骤记录

    # ---- 回答生成 ----
    sources: list[dict]                  # Source 引用列表
    tokens_used: int                     # Token 消耗
    model_name: str                      # 使用的模型名

    # ---- 最终输出 ----
    final_response: str                  # 最终回答文本
    error: Optional[str]                 # 错误信息
    done: bool                           # 是否完成


def create_initial_state(
    user_id: str,
    conversation_id: str,
    message: str,
    history: list[dict] | None = None,
    permission_context: dict | None = None,
    model_name: str = "deepseek-chat",
) -> InternState:
    """创建 LangGraph 初始状态。"""
    return InternState(
        user_id=user_id,
        conversation_id=conversation_id,
        message=message,
        history=history or [],
        permission_context=permission_context or {},
        intent="chat",
        intent_confidence=0.0,
        clarify_questions=[],
        clarify_round=0,
        pending_clarify=False,
        retrieved_docs=[],
        filtered_docs=[],
        rag_context="",
        generated_sql="",
        sql_security_passed=False,
        sql_security_detail={},
        executed_sql="",
        sql_result=None,
        sql_error=None,
        traces=[],
        sources=[],
        tokens_used=0,
        model_name=model_name,
        final_response="",
        error=None,
        done=False,
    )
