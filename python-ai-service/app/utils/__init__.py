"""工具函数集合。

SQL 格式化、Markdown 辅助、时间处理等通用工具。
"""

import re
from typing import Any


def format_sql_result(result: Any, max_rows: int = 50) -> str:
    """将 SQL 查询结果格式化为可读字符串。"""
    if isinstance(result, dict):
        rows = result.get("rows", [])
        cols = result.get("columns", [])
        if not rows:
            return "(查询结果为空)"

        lines = []
        if cols:
            lines.append(" | ".join(str(c) for c in cols))
            lines.append("-" * len(lines[0]))
        for row in rows[:max_rows]:
            if isinstance(row, dict):
                lines.append(" | ".join(str(v) for v in row.values()))
            elif isinstance(row, (list, tuple)):
                lines.append(" | ".join(str(v) for v in row))
            else:
                lines.append(str(row))
        if len(rows) > max_rows:
            lines.append(f"... (共 {len(rows)} 行，仅显示前{max_rows}行)")
        return chr(10).join(lines)

    return str(result)[:2000]


def truncate_text(text: str, max_len: int = 200) -> str:
    """截断文本，添加省略号。"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def extract_sql_from_llm(text: str) -> str:
    """从 LLM 响应中提取纯 SQL 语句。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split(chr(10))
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = chr(10).join(lines).strip()
    for keyword in ["SELECT", "select", "WITH", "with"]:
        idx = text.upper().find(keyword.upper())
        if idx > 0:
            text = text[idx:]
            break
    return text.strip()
