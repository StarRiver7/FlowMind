
"""反问澄清节点 - 小SU 主动向老师确认信息。

当意图识别判定信息不足时进入此节点。
生成结构化反问，支持多轮参数收集。
"""

import time
from app.graph.state import InternState
from app.llm.gateway import llm_gateway
from app.prompts.internsu_prompts import InternSUPrompts, PromptType, get_prompt
from app.core.logger import get_logger

logger = get_logger(__name__)


async def clarify_node(state: InternState) -> InternState:
    """反问澄清节点。

    根据缺失的信息，用 LLM 生成礼貌的结构化反问。
    """
    step_start = time.time()
    state["traces"] = state.get("traces", []) + [{
        "step": "clarification",
        "status": "running",
        "step_order": 2,
    }]

    message = state["message"]
    history = state.get("history", [])

    # 构建上下文
    clarify_prompt = InternSUPrompts.render(
        PromptType.CLARIFY,
        user_message=message,
        missing_info=_describe_missing(message),
    )

    messages = [
        InternSUPrompts.build_system_message(),
        {"role": "user", "content": clarify_prompt},
    ]
    if history:
        messages = [messages[0]] + history[-6:] + [messages[1]]

    try:
        resp = await llm_gateway.chat(messages, temperature=0.5, max_tokens=512)
        final_response = resp.content.strip()
        state["tokens_used"] = resp.usage.get("total_tokens", 0) if resp.usage else 0
    except Exception as e:
        logger.error(f"Clarify generation failed: {e}")
        final_response = "收到老师～我不太确定您想问什么，能再说详细一点吗？"

    state["final_response"] = final_response
    state["intent"] = "clarify"
    state["done"] = True

    # 更新 trace
    duration_ms = int((time.time() - step_start) * 1000)
    state["traces"][-1] = {
        "step": "clarification",
        "status": "completed",
        "step_order": 2,
        "detail": {"questions_count": 2},
        "duration_ms": duration_ms,
    }

    return state


def _describe_missing(message: str) -> str:
    """描述缺失的信息（简单启发式）。"""
    missing = []

    if not any(w in message for w in ["今天", "昨天", "本周", "本月", "上月", "最近", "今年",
                                         "去年", "季度", "Q1", "Q2", "过去"]):
        missing.append("时间范围（比如本月？上季度？今年？）")
    if not any(w in message for w in ["部门", "全公司", "组", "团队"]):
        missing.append("部门或范围（比如全公司？技术部？）")
    if not any(w in message for w in ["多少", "数量", "统计", "查询", "销售", "金额", "人数",
                                        "排名", "汇总"]):
        missing.append("具体查询指标（比如人数？销售额？订单数？）")
    if not missing:
        missing.append("更具体的查询条件")

    return "; ".join(missing)
