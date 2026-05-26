"""
InternSU AI 实习生人格 System Prompt 入口。

本模块是 prompts/internsu_prompts.py 的便捷别名，
提供用户指定的文件名 system_prompt.py。
"""

from app.prompts.internsu_prompts import (
    InternSUPrompts,
    get_prompt,
    PROMPTS,
    PromptType,
    SYSTEM_PROMPT,
    RAG_PROMPT,
    SQL_GENERATE_PROMPT,
    SQL_SUMMARY_PROMPT,
    CLARIFY_PROMPT,
    INTENT_PROMPT,
)

__all__ = [
    "InternSUPrompts",
    "get_prompt",
    "PROMPTS",
    "PromptType",
    "SYSTEM_PROMPT",
    "RAG_PROMPT",
    "SQL_GENERATE_PROMPT",
    "SQL_SUMMARY_PROMPT",
    "CLARIFY_PROMPT",
    "INTENT_PROMPT",
]
