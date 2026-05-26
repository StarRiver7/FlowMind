
"""意图识别节点 - 判断老师想问什么。

支持5种意图分类:
  - chat: 闲聊、问候
  - rag: 需要查询公司文档知识库
  - sql: 需要查询数据库数据
  - clarify: 信息不足，需要反问澄清
  - document_summary: 文档总结（MVP 暂简化处理）

同时判断是否需要澄清:
  - SQL 查询缺少时间范围/部门/指标 -> clarify
  - 关键词太少 -> clarify
  - 上轮刚澄清过 -> 直接执行
"""

import time
from app.graph.state import InternState
from app.llm.gateway import llm_gateway
from app.prompts.internsu_prompts import InternSUPrompts, PromptType, get_prompt
from app.core.logger import get_logger

logger = get_logger(__name__)

VALID_INTENTS = {"chat", "rag", "sql", "clarify"}

# 信息不足判定: 意图 -> 必需实体
REQUIRED_ENTITIES = {
    "sql": ["metric", "time_range"],  # 至少要知道查什么和时间
    "rag": [],
    "chat": [],
    "clarify": [],
}


def _check_info_sufficiency(intent: str, message: str, history: list[dict]) -> tuple[bool, str]:
    """检查信息是否足够执行。

    Returns:
        (is_sufficient, missing_info_description)
    """
    # 如果上一轮是 clarify，本轮直接执行
    if history:
        last_msg = history[-1] if history else {}
        if last_msg.get("role") == "assistant" and _is_clarify_response(last_msg.get("content", "")):
            return True, ""

    # SQL 需要判断
    if intent == "sql":
        # 简单启发式: 检查是否包含数字查询相关的关键词和时间/部门限定
        has_metric = any(w in message for w in ["多少", "数量", "统计", "查询", "销售", "金额", "人数",
                                                  "排名", "TOP", "top", "汇总", "总计", "平均"])
        has_time = any(w in message for w in ["今天", "昨天", "本周", "本月", "上月", "上个月",
                                                 "今年", "去年", "季度", "Q1", "Q2", "最近", "过去"])
        has_scope = any(w in message for w in ["部门", "全公司", "组", "团队", "产品", "项目", "技术", "前端", "后端", "运维", "测试", "销售", "市场", "财务", "人事", "行政",
                                                  "各", "每个", "按"])

        missing = []
        if not has_metric:
            missing.append("需要查询的具体指标（如人数、销售额、订单数）")
        if not has_time:
            missing.append("时间范围（如本月、上季度、今年）")
        if not has_scope:
            missing.append("部门或范围（如技术部、全公司）")

        if missing:
            return False, ", ".join(missing)

    # RAG: 关键词太少
    if intent == "rag":
        keywords = [w for w in message if len(w) >= 2]
        if len(keywords) < 3:
            return False, "问题描述不够具体，我无法确定您想查什么资料"

    return True, ""


def _is_clarify_response(content: str) -> bool:
    """检查是否是 clarify 回复。"""
    return any(phrase in content for phrase in ["收到老师～", "默认", "确认", "请问"])


async def intent_node(state: InternState) -> InternState:
    """意图识别节点。

    1. 用 LLM 分类用户意图
    2. 检查信息是否充分
    3. 不充分则标记为 clarify
    """
    step_start = time.time()
    trace = {
        "step": "intent_recognition",
        "status": "running",
        "step_order": 1,
        "started_at": None,
    }
    state["traces"] = state.get("traces", []) + [trace]

    message = state["message"]
    history = state.get("history", [])

    # Step 1: LLM 意图分类
    try:
        intent_prompt = InternSUPrompts.render(PromptType.INTENT, user_message=message)
        messages = [{"role": "user", "content": intent_prompt}]
        resp = await llm_gateway.chat(messages, temperature=0.0, max_tokens=10)
        intent_raw = resp.content.strip().lower()
        intent = intent_raw if intent_raw in VALID_INTENTS else "chat"
        logger.debug(f"Intent: {intent} for '{message[:50]}...'")
    except Exception as e:
        logger.warning(f"Intent classification fallback: {e}")
        intent = "chat"

    # Step 2: 检查信息充分性
    is_sufficient, missing_info = _check_info_sufficiency(intent, message, history)

    if not is_sufficient and intent in ("sql", "rag"):
        intent = "clarify"
        state["clarify_round"] = state.get("clarify_round", 0) + 1
        state["pending_clarify"] = True
    else:
        state["pending_clarify"] = False

    state["intent"] = intent
    state["intent_confidence"] = 0.9

    # 更新 trace
    duration_ms = int((time.time() - step_start) * 1000)
    state["traces"][-1] = {
        "step": "intent_recognition",
        "status": "completed",
        "step_order": 1,
        "detail": {"intent": intent, "confidence": 0.9},
        "duration_ms": duration_ms,
    }

    return state
