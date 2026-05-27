"""Query Rewrite — LLM-powered query optimization for better retrieval.

Transforms vague user queries into search-optimized forms.
Uses DeepSeek LLM via the existing LLM gateway.

Examples:
  "请假制度" → "公司员工请假制度 年假 调休 病假 规则"
  "报销" → "费用报销流程 差旅报销 审批规则 发票要求"
"""

from app.llm.gateway import llm_gateway
from app.core.logger import get_logger

logger = get_logger(__name__)

REWRITE_PROMPT = """You are a search query optimizer. Your task is to rewrite a user's search query to improve retrieval quality.

Rules:
1. Expand abbreviations and vague terms into specific keywords
2. Add synonyms and related terms
3. Keep the original intent
4. Return ONLY the rewritten query, no explanations
5. Keep it under 200 characters
6. Use Chinese when the query is in Chinese

User query: {query}

Rewritten query:"""


class QueryRewriter:
    """LLM-based query rewriter for better retrieval recall."""

    def __init__(self, model: str = "deepseek-chat"):
        self._model = model

    async def rewrite(self, query: str) -> str:
        """Rewrite a user query for optimal retrieval.

        Returns the original query if LLM fails or if query is already specific.
        """
        if not query or len(query.strip()) < 3:
            return query

        # Skip rewrite for already-specific queries (>30 chars likely specific)
        if len(query) > 50:
            return query

        try:
            prompt = REWRITE_PROMPT.format(query=query)
            rewritten = await llm_gateway.chat(
                messages=[{"role": "user", "content": prompt}],
                model=self._model,
                max_tokens=100,
                temperature=0.3,
            )
            rewritten = rewritten.strip().strip('"').strip("'")
            if rewritten and len(rewritten) >= len(query):
                logger.debug(f"[QueryRewrite] '{query}' → '{rewritten}'")
                return rewritten
        except Exception as e:
            logger.warning(f"[QueryRewrite] LLM rewrite failed: {e}")

        return query

    async def rewrite_with_keywords(self, query: str) -> dict:
        """Rewrite query and extract standalone keywords.

        Returns {"rewritten": str, "keywords": [str]}
        """
        rewritten = await self.rewrite(query)

        # Simple keyword extraction
        import re
        keywords = list(set(
            kw.strip() for kw in re.split(r"[，,、\s]+", rewritten)
            if len(kw.strip()) >= 2
        ))

        return {"rewritten": rewritten, "keywords": keywords}


query_rewriter = QueryRewriter()
