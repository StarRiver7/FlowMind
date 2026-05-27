
"""Clarify 反问节点。

职责:
  当意图识别判定信息不足时，生成礼貌的结构化反问。
  支持多轮反问和参数槽位收集。
"""

import time
from app.graph.state import InternState
from app.llm.gateway import llm_gateway
from app.core.logger import get_logger

logger = get_logger(__name__)


CLARIFY_SYSTEM_PROMPT = """你是小SU，刚入职的AI实习生。

老师问了一个问题，但信息不够完整。你需要礼貌地确认细节。

规则:
1. 永远以"收到老师～"开头
2. 列出需要确认的信息（编号列表，不超过3个问题）
3. 每个问题提供默认选项（如果可以确定）
4. 结尾加上"如果默认值没问题，回复'确认'就可以～"
5. 语气礼貌、清晰，不要道歉

禁止:
- 不要说"作为AI助手"
- 不要只问开放性问题，要给选项
- 不要超过3个问题"""


async def clarify_node(state: InternState) -> InternState:
    """反问澄清节点。

    生成结构化的反问消息，记录到 final_answer。
    标记 clarify_pending=True，等待用户下一轮输入。
    """
    t0 = time.time()
    state["current_node"] = "clarify_node"

    state["trace_steps"] = state.get("trace_steps", []) + [{
        "node": "clarify_node",
        "message": "正在确认信息是否完整...",
        "status": "running",
        "timestamp": _now(),
    }]

    message = state["user_message"]
    history = state.get("conversation_context", [])

    # 构建反问 Prompt
    user_prompt = (
        f"老师的问题: {message}\n\n"
        f"请生成礼貌的反问，确认缺失的信息。"
    )

    messages = [
        {"role": "system", "content": CLARIFY_SYSTEM_PROMPT},
    ]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_prompt})

    try:
        resp = await llm_gateway.chat(messages, temperature=0.5, max_tokens=512)
        clarify_text = resp.content.strip()
        state["tokens_used"] = state.get("tokens_used", 0) + (
            resp.usage.get("total_tokens", 0) if resp.usage else 0
        )
    except Exception as e:
        logger.error(f"Clarify generation failed: {e}")
        clarify_text = "收到老师～我不太确定您想问什么，能再说详细一点吗？"

    state["clarify_question"] = clarify_text
    state["clarify_pending"] = True
    state["final_answer"] = clarify_text
    state["done"] = True

    duration_ms = int((time.time() - t0) * 1000)
    state["trace_steps"][-1] = {
        "node": "clarify_node",
        "message": "需要向老师确认几个信息",
        "status": "completed",
        "detail": {
            "clarify_round": state.get("clarify_round", 1),
        },
        "duration_ms": duration_ms,
        "timestamp": _now(),
    }

    logger.info(f"ClarifyNode: round={state.get('clarify_round', 1)}, question_len={len(clarify_text)}")
    return state


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
