
"""意图识别节点。

职责:
  1. 用 LLM 分类用户意图 (chat/clarify/rag/sql)
  2. 检查信息是否充分，决定是否需要反问澄清
  3. 写入 trace_steps
"""

import time
from app.graph.state import InternState
from app.llm.gateway import llm_gateway
from app.core.logger import get_logger

logger = get_logger(__name__)

# 意图分类 System Prompt
INTENT_CLASSIFY_PROMPT = """分析用户消息的意图。只回复一个类别名称。

类别说明:
- chat: 闲聊、问候、简单问答、不涉及数据查询和文档检索
- rag: 需要查询公司文档/知识库的问题（政策、规章、流程说明、how-to 等）
- sql: 需要查询数据库的统计/数量/排名类问题（销售额、人数、订单数等）
- clarify: 问题信息严重不足，无法判断意图，需要反问澄清

判断要点:
- 如果问题中同时包含 统计指标 + 时间范围 + 部门范围 → sql
- 如果问题只是"查一下数据"/"帮我查"/"看看"且缺少具体条件 → clarify
- 如果问题涉及公司政策、规定、流程名称 → rag
- 如果问题只是一般性聊天 → chat

用户消息: {user_message}

意图类别:"""


async def intent_node(state: InternState) -> InternState:
    """意图识别节点。

    工作流程:
      1. 调用 LLM 分类意图
      2. 结构化检查信息充分性
      3. 决定 clarify_required
      4. 记录 trace_step
    """
    t0 = time.time()
    state["current_node"] = "intent_node"

    # 记录开始
    state["trace_steps"] = state.get("trace_steps", []) + [{
        "node": "intent_node",
        "message": "正在理解老师的问题...",
        "status": "running",
        "timestamp": _now(),
    }]

    message = state["user_message"]
    history = state.get("conversation_context", [])

    # ---- Step 1: LLM 意图分类 ----
    try:
        classify_msg = INTENT_CLASSIFY_PROMPT.format(user_message=message)
        resp = await llm_gateway.chat(
            [{"role": "user", "content": classify_msg}],
            temperature=0.0, max_tokens=10,
        )
        intent = resp.content.strip().lower()
        if intent not in ("chat", "rag", "sql", "clarify"):
            intent = "chat"
        state["intent"] = intent
        state["intent_confidence"] = 0.9
        logger.info(f"IntentNode: '{message[:40]}...' → {intent}")
    except Exception as e:
        logger.warning(f"Intent classification fallback: {e}")
        state["intent"] = "chat"
        state["intent_confidence"] = 0.3

    # ---- Step 2: 信息充分性检查 ----
    clarify_required = _check_clarify_needed(state["intent"], message, history)
    state["clarify_required"] = clarify_required

    if clarify_required:
        # Keep original intent for slot schema lookup
        state["clarify_round"] = state.get("clarify_round", 0) + 1

    # ---- 记录完成 ----
    duration_ms = int((time.time() - t0) * 1000)
    state["trace_steps"][-1] = {
        "node": "intent_node",
        "message": f"已识别问题类型: {_intent_cn(state['intent'])}",
        "status": "completed",
        "detail": {
            "intent": state["intent"],
            "confidence": state["intent_confidence"],
            "clarify_required": clarify_required,
        },
        "duration_ms": duration_ms,
        "timestamp": _now(),
    }

    return state


def _check_clarify_needed(intent: str, message: str, history: list[dict]) -> bool:
    """检查是否需要反问澄清。

    判定规则:
      1. intent 本身是 clarify → 需要
      2. SQL 类问题缺少关键信息 → 需要
      3. RAG 类问题关键词太少 → 需要
      4. 上一轮刚澄清过 → 不需要 (用户正在回答问题)
    """
    if intent == "clarify":
        return True

    # 如果上一轮是 clarify，本轮用户正在回答 → 不要再次反问
    last_msg = history[-1] if history else {}
    if last_msg.get("role") == "assistant" and _looks_like_clarify_response(last_msg.get("content", "")):
        return False

    if intent == "sql":
        has_metric = any(w in message for w in
            ["多少", "数量", "统计", "查询", "销售", "金额", "人数", "排名",
             "TOP", "汇总", "总计", "平均", "增长率"])
        has_time = any(w in message for w in
            ["今天", "昨天", "本周", "本月", "上月", "上个月", "今年", "去年",
             "季度", "Q1", "Q2", "最近", "过去", "年度"])
        has_scope = any(w in message for w in
            ["部门", "全公司", "组", "团队", "产品", "项目", "各", "每个", "按",
             "技术", "前端", "后端", "运维", "测试", "销售", "市场", "财务", "人事"])

        if not (has_metric and has_time and has_scope):
            return True

    if intent == "rag":
        if len(message) < 5:
            return True

    return False




def _check_info_sufficiency(intent: str, message: str, history: list[dict]) -> tuple[bool, list[str]]:
    """Compatibility wrapper: returns (is_sufficient, missing_fields).

    Wraps _check_clarify_needed and infers missing fields from the message.
    """
    clarify_needed = _check_clarify_needed(intent, message, history)
    if not clarify_needed:
        return True, []

    # Infer what's missing
    missing = []
    if intent == 'sql':
        has_metric = any(w in message for w in
            ['???', '???', '??', '??', '???', '??', '???', '???',
             'TOP', '???', '??', '???', '????'])
        has_time = any(w in message for w in
            ['???', '???', '??', '??', '???', '????', '???', '???',
             '???', 'Q1', 'Q2', '???', '???', '???'])
        has_scope = any(w in message for w in
            ['???', '????', '?', '???', '???', '???', '?', '???', '?',
             '???', '??', '??', '???', '???', '???', '???', '???', '???'])
        if not has_metric:
            missing.append('?????')
        if not has_time:
            missing.append('??????')
        if not has_scope:
            missing.append('??????')
    elif intent == 'rag':
        missing.append('???????')
    elif intent == 'clarify':
        missing.append('????')
    return False, missing

def _looks_like_clarify_response(content: str) -> bool:
    """检查是否是反问格式的回复。"""
    return any(kw in content for kw in ["收到老师", "确认", "请问", "需要确认"])


def _intent_cn(intent: str) -> str:
    """意图中文映射。"""
    return {
        "chat": "一般对话",
        "rag": "知识检索",
        "sql": "数据查询",
        "clarify": "需要确认",
        "unclear": "不明确",
    }.get(intent, intent)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
