
"""最终回答生成节点。

根据意图和中间结果生成最终回答:
  - chat: 直接 LLM 回复
  - rag: 使用 RAG 上下文生成
  - sql: 使用 SQL 结果生成自然语言总结
"""

import time
from app.graph.state import InternState
from app.llm.gateway import llm_gateway
from app.prompts.internsu_prompts import InternSUPrompts, PromptType
from app.core.logger import get_logger

logger = get_logger(__name__)


async def answer_node(state: InternState) -> InternState:
    """最终回答生成节点。"""
    step_start = time.time()
    state["traces"] = state.get("traces", []) + [{
        "step": "answer_generation",
        "status": "running",
        "step_order": 99,  # 最后一步
    }]

    intent = state.get("intent", "chat")
    message = state["message"]
    history = state.get("history", [])
    model = state.get("model_name", "deepseek-chat")

    try:
        # 构建 messages
        system_msg = InternSUPrompts.build_system_message()
        messages = [system_msg]

        if history:
            messages.extend(history[-10:])  # 最近5轮

        if intent == "rag" and state.get("rag_context"):
            # RAG 上下文已经在 render 时包含了 system prompt
            messages = [
                {"role": "system", "content": state["rag_context"]},
            ]

        elif intent == "sql" and state.get("sql_result") is not None:
            sql_summary_prompt = InternSUPrompts.render(
                PromptType.SQL_SUMMARY,
                user_message=message,
                executed_sql=state.get("executed_sql", ""),
                query_result=_format_sql_result(state["sql_result"]),
            )
            messages.append({"role": "user", "content": sql_summary_prompt})

        else:
            messages.append({"role": "user", "content": message})

        resp = await llm_gateway.chat(messages, model=model, temperature=0.7, max_tokens=2048)
        final_response = resp.content.strip()
        state["tokens_used"] = state.get("tokens_used", 0) + (
            resp.usage.get("total_tokens", 0) if resp.usage else 0
        )

    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        final_response = "收到老师～我刚刚处理任务时遇到一点问题，请稍后再试～"
        state["error"] = str(e)

    state["final_response"] = final_response
    state["done"] = True

    duration_ms = int((time.time() - step_start) * 1000)
    state["traces"][-1] = {
        "step": "answer_generation",
        "status": "completed",
        "step_order": 99,
        "detail": {"model": model, "tokens": state.get("tokens_used", 0)},
        "duration_ms": duration_ms,
    }

    return state


def _format_sql_result(result) -> str:
    """格式化 SQL 结果为可读字符串。"""
    if isinstance(result, dict):
        rows = result.get("rows", [])
        cols = result.get("columns", [])
        if not rows:
            return "(查询结果为空)"

        lines = []
        if cols:
            lines.append(" | ".join(str(c) for c in cols))
            lines.append("-" * len(lines[0]))
        for row in rows[:50]:
            if isinstance(row, dict):
                lines.append(" | ".join(str(v) for v in row.values()))
            elif isinstance(row, (list, tuple)):
                lines.append(" | ".join(str(v) for v in row))
            else:
                lines.append(str(row))
        if len(rows) > 50:
            lines.append(f"... (共 {len(rows)} 行，仅显示前50行)")
        return "\n".join(lines)

    return str(result)[:2000]
