
"""SQL Agent 节点 - NL2SQL 生成、安全检查、执行。

包含三道防线:
  防线1: sqlparse 语法校验
  防线2: 危险关键词拦截
  防线3: 只读从库执行
"""

import time
from app.graph.state import InternState
from app.llm.gateway import llm_gateway
from app.sql_agent.generator import sql_generator
from app.sql_agent.security import sql_security
from app.sql_agent.executor import sql_executor
from app.prompts.internsu_prompts import InternSUPrompts, PromptType
from app.core.logger import get_logger

logger = get_logger(__name__)


async def sql_node(state: InternState) -> InternState:
    """SQL 生成 + 安全校验 + 执行节点。"""
    query = state["message"]

    # ---- Sub-step 1: SQL 生成 ----
    t1 = time.time()
    state["traces"] = state.get("traces", []) + [{
        "step": "sql_generation",
        "status": "running",
        "step_order": 2,
    }]

    try:
        generated_sql = await sql_generator.generate(query)
        state["generated_sql"] = generated_sql
        state["traces"][-1] = {
            "step": "sql_generation",
            "status": "completed",
            "step_order": 2,
            "detail": {"sql_preview": generated_sql[:200]},
            "duration_ms": int((time.time() - t1) * 1000),
        }
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        state["error"] = f"SQL生成失败: {e}"
        state["final_response"] = ("收到老师～我在尝试查询数据库时遇到了一点问题，"
                                    "可能是表结构不支持这个查询。您可以换个方式问吗？")
        state["done"] = True
        state["traces"][-1] = {"step": "sql_generation", "status": "failed",
                                "step_order": 2, "detail": {"error": str(e)}}
        return state

    # ---- Sub-step 2: 安全校验 ----
    t2 = time.time()
    state["traces"] = state.get("traces", []) + [{
        "step": "sql_security_check",
        "status": "running",
        "step_order": 3,
    }]

    security_result = sql_security.check(generated_sql)
    state["sql_security_passed"] = security_result["passed"]
    state["sql_security_detail"] = security_result

    if not security_result["passed"]:
        logger.warning(f"SQL blocked: {security_result['reason']}")
        state["error"] = f"SQL安全拦截: {security_result['reason']}"
        state["final_response"] = ("收到老师～这个查询涉及到了我不允许执行的操作（"
                                   f"{security_result['reason']}），我只能执行只读查询。"
                                   "要不换个方式问？")
        state["done"] = True
        state["traces"][-1] = {
            "step": "sql_security_check", "status": "completed",
            "step_order": 3,
            "detail": {"passed": False, "reason": security_result["reason"]},
        }
        return state

    state["traces"][-1] = {
        "step": "sql_security_check", "status": "completed",
        "step_order": 3,
        "detail": {"passed": True},
        "duration_ms": int((time.time() - t2) * 1000),
    }

    # ---- Sub-step 3: 执行 SQL ----
    t3 = time.time()
    state["traces"] = state.get("traces", []) + [{
        "step": "sql_execution",
        "status": "running",
        "step_order": 4,
    }]

    try:
        exec_result = await sql_executor.execute(security_result["sanitized_sql"])
        state["executed_sql"] = security_result["sanitized_sql"]
        state["sql_result"] = exec_result
        state["sql_error"] = None

        duration_ms = int((time.time() - t3) * 1000)
        row_count = exec_result.get("row_count", 0) if isinstance(exec_result, dict) else 0
        state["traces"][-1] = {
            "step": "sql_execution", "status": "completed",
            "step_order": 4,
            "detail": {"rows": row_count, "duration_ms": duration_ms},
            "duration_ms": duration_ms,
        }
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        state["sql_error"] = str(e)
        state["final_response"] = ("收到老师～SQL 执行时出错了。可能是数据库暂时不可用，"
                                    "请稍后再试～")
        state["done"] = True
        state["traces"][-1] = {"step": "sql_execution", "status": "failed",
                                "step_order": 4, "detail": {"error": str(e)}}
        return state

    return state
