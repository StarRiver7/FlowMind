"""Source Formatter — unified display formatting for citations.

Produces consistent, frontend-ready citation displays
in multiple formats:
  - inline: "[1] 《员工手册》第5页"
  - list: numbered reference list
  - compact: minimal for tight UIs
  - markdown: for LLM context injection
"""

from typing import Optional
from app.rag.citation.citation_models import Citation, CitationSet
from app.core.logger import get_logger

logger = get_logger(__name__)


class SourceFormatter:
    """Format citations for various display contexts.

    Usage:
        fmt = SourceFormatter()
        inline = fmt.format_inline(citations)       # → "[1][2][3]"
        ref_list = fmt.format_reference_list(citations)  # → "参考来源:\n[1] ..."
        md = fmt.format_markdown(citations, query)  # → LLM context
    """

    # Configuration
    citation_style: str = "bracket"  # bracket | superscript | parenthetical

    def format_inline(self, citations: list[Citation]) -> str:
        """Inline citation markers like [1][2][3]."""
        if not citations:
            return ""
        markers = [c.inline_marker() for c in citations]
        return "".join(markers)

    def format_reference_list(
        self,
        citations: list[Citation],
        *,
        include_score: bool = False,
        include_kb: bool = True,
    ) -> str:
        """Numbered reference list for end-of-answer display.

        Example:
            参考来源:
            [1] 《员工手册》第5页 - HR知识库
            [2] 《考勤规范.pdf》第3页 - 行政部
        """
        if not citations:
            return ""

        lines = ["**参考来源:**"]
        for c in citations:
            parts = [f"[{c.citation_id}] {c.display_ref()}"]
            if include_kb and c.knowledge_base:
                parts.append(f"- {c.knowledge_base}")
            if include_score:
                parts.append(f"(相关度: {c.relevance_score:.0%})")
            lines.append(" ".join(parts))

        return "\n".join(lines)

    def format_markdown(
        self,
        citations: list[Citation],
        query: str = "",
    ) -> str:
        """Markdown-formatted context for LLM prompt injection.

        Example:
            ## 参考来源
            - **[1]** 《员工手册》第5页 | HR知识库 | 相关度: 94%
              > 年假需提前3天向直属领导申请...
        """
        if not citations:
            return "（无参考来源）"

        lines = ["## 参考来源"]
        for c in citations:
            # Header line
            header = f"- **[{c.citation_id}]** {c.display_ref()}"
            if c.knowledge_base:
                header += f" | {c.knowledge_base}"
            header += f" | 相关度: {c.relevance_score:.0%}"
            lines.append(header)

            # Quote
            if c.quote_text:
                lines.append(f"  > {c.quote_text}")

        return "\n".join(lines)

    def format_compact(
        self,
        citations: list[Citation],
    ) -> str:
        """Compact format for tight UI spaces (e.g., sidebar, tooltip)."""
        if not citations:
            return ""
        parts = []
        for c in citations:
            parts.append(f"[{c.citation_id}] {c.document_name} p.{c.page_number}")
        return " · ".join(parts)

    def format_llm_context_block(
        self,
        citations: list[Citation],
        *,
        max_sources: int = 5,
    ) -> str:
        """Build a citation-aware context block for LLM system prompt.

        Includes both content and inline citation markers so the LLM
        can reference sources naturally in its answer.
        """
        if not citations:
            return ""

        lines = ["## 知识库检索结果（含引用来源）"]
        lines.append("请在回答中引用来源，格式为 [来源N] 。")
        lines.append("")

        for c in citations[:max_sources]:
            lines.append(f"---")
            lines.append(f"[来源{c.citation_id}] {c.display_ref()}")
            if c.title_path:
                lines.append(f"章节: {c.title_path}")
            lines.append(f"内容:")
            lines.append(c.full_content[:1000])
            lines.append("")

        return "\n".join(lines)

    def format_frontend_response(
        self,
        answer: str,
        citation_set: CitationSet,
    ) -> dict:
        """Build complete frontend-ready response with citations.

        Returns a dict suitable for API response:
        {
            "answer": "...",
            "citations": [...],
            "reference_list": "...",
            "trust_level": "high",
        }
        """
        return {
            "answer": answer,
            "citations": [c.to_dict() for c in citation_set.citations],
            "reference_list": self.format_reference_list(
                citation_set.citations, include_kb=True
            ),
            "inline_markers": self.format_inline(citation_set.citations),
            "trust_level": citation_set.trust_level,
            "primary_source": citation_set.primary_source.to_dict()
            if citation_set.primary_source else None,
        }


source_formatter = SourceFormatter()
