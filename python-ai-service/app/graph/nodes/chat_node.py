
"""Chat 聊天节点。

职责:
  构建 System Prompt + 对话历史 + 用户消息，调用 LLM 生成回答。
  支持: 多轮对话、流式输出 (由上层 SSE handler 处理)。
"""

import time
from app.graph.state import InternState
from app.llm.gateway import llm_gateway
from app.core.logger import get_logger

logger = get_logger(__name__)

INTERNSU_SYSTEM_PROMPT = """你是小SU，一个刚入职的AI实习生，同事们都叫你"小SU"。

## 你的身份
- 你是公司里最年轻的成员，刚刚开始实习
- 你的职责是帮老师们（同事们）查询信息、整理资料、分析数据
- 你对公司充满热情，做事认真负责

## 对话规则
- 永远称呼用户为"老师"
- 常用表达: "收到老师～" "好的老师～" "小SU帮您查一下～"
- 不确定的事情不会乱猜，会主动问清楚
- 回答简洁准确，不啰嗦
- 禁止说"作为AI助手"、"根据我的知识库"

## 回答风格
- 知识查询: 引用公司文档，标注来源
- 数据查询: 说明执行了什么查询
- 不知道: 诚实告知，建议联系相关部门"""


async def chat_node(state: InternState) -> InternState:
    """聊天生成节点。

    构建完整的 messages 数组并调用 LLM 推理。
    """
    t0 = time.time()
    state["current_node"] = "chat_node"

    state["trace_steps"] = state.get("trace_steps", []) + [{
        "node": "chat_node",
        "message": "正在整理回答...",
        "status": "running",
        "timestamp": _now(),
    }]

    message = state["user_message"]
    history = state.get("conversation_context", [])
    model = state.get("model_name", "deepseek-chat")

    # 构建完整 messages
    messages = [{"role": "system", "content": INTERNSU_SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-10:])  # 最近5轮
    messages.append({"role": "user", "content": message})

    state["system_prompt"] = INTERNSU_SYSTEM_PROMPT

    try:
        resp = await llm_gateway.chat(messages, model=model, temperature=0.7, max_tokens=2048)
        answer = resp.content.strip()
        state["tokens_used"] = state.get("tokens_used", 0) + (
            resp.usage.get("total_tokens", 0) if resp.usage else 0
        )
        logger.info(f"ChatNode: answer_len={len(answer)}, model={model}")
    except Exception as e:
        logger.error(f"ChatNode LLM error: {e}")
        answer = "收到老师～我刚刚处理任务时遇到一点问题，请稍后再试～"
        state["error"] = str(e)

    state["final_answer"] = answer
    state["done"] = True

    duration_ms = int((time.time() - t0) * 1000)
    state["trace_steps"][-1] = {
        "node": "chat_node",
        "message": "回答已生成",
        "status": "completed",
        "detail": {"model": model, "tokens": state.get("tokens_used", 0)},
        "duration_ms": duration_ms,
        "timestamp": _now(),
    }

    return state


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
