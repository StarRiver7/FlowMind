from jinja2 import Template
from typing import Any


class PromptBuilder:
    """Prompt组装器 — 按固定层级组装System/Context/History/User Message"""

    # 默认系统Prompt模板
    DEFAULT_SYSTEM_PROMPT = (
        "You are an enterprise AI assistant. "
        "Answer accurately based on provided context. "
        "If you don\'t know, say so. "
        "Cite sources when using context documents."
    )

    # RAG增强Prompt模板
    RAG_SYSTEM_PROMPT = (
        "You are an enterprise knowledge assistant. "
        "Answer the user\'s question based ONLY on the following context documents.\n"
        "If the context does not contain relevant information, say so.\n"
        "Always cite the source document when referencing context.\n\n"
        "Context:\n"
        "{% for doc in context_docs %}"
        "[Source: {{ doc.source }}] {{ doc.content }}\n\n"
        "{% endfor %}"
    )

    # SQL Agent系统Prompt
    SQL_SYSTEM_PROMPT = (
        "You are a SQL query assistant. "
        "Given the database schema and user question, generate a valid SQL query.\n"
        "Rules:\n"
        "1. Only SELECT statements allowed\n"
        "2. Always use LIMIT for potentially large result sets\n"
        "3. Use table aliases for readability\n\n"
        "Database Schema:\n"
        "{{ schema }}\n"
    )

    def __init__(self, system_template: str | None = None):
        self._system_template = system_template or self.DEFAULT_SYSTEM_PROMPT

    def build(
        self,
        user_message: str,
        history: list[dict] | None = None,
        context: dict[str, Any] | None = None,
        system_override: str | None = None,
    ) -> list[dict]:
        """构建完整的消息列表"""
        messages = []

        # 1. System Prompt
        system_tmpl = system_override or self._system_template
        if context:
            try:
                tmpl = Template(system_tmpl)
                system_content = tmpl.render(**context)
            except Exception:
                system_content = system_tmpl
        else:
            system_content = system_tmpl

        messages.append({"role": "system", "content": system_content})

        # 2. 历史消息（最近N轮）
        if history:
            messages.extend(history)

        # 3. 用户消息
        messages.append({"role": "user", "content": user_message})

        return messages

    def build_rag_prompt(
        self,
        user_message: str,
        retrieved_docs: list[dict],
        history: list[dict] | None = None,
    ) -> list[dict]:
        """构建RAG增强的Prompt"""
        context = {"context_docs": retrieved_docs}
        return self.build(
            user_message=user_message,
            history=history,
            context=context,
            system_override=self.RAG_SYSTEM_PROMPT,
        )

    def build_sql_prompt(
        self,
        user_message: str,
        schema: str,
        history: list[dict] | None = None,
    ) -> list[dict]:
        """构建SQL Agent的Prompt"""
        context = {"schema": schema}
        return self.build(
            user_message=user_message,
            history=history,
            context=context,
            system_override=self.SQL_SYSTEM_PROMPT,
        )


prompt_builder = PromptBuilder()
