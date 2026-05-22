from dataclasses import dataclass
from enum import Enum


class IntentType(str, Enum):
    CHITCHAT = "chitchat"
    KNOWLEDGE = "knowledge"
    TOOL_CALL = "tool_call"
    SQL_QUERY = "sql_query"


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float


class IntentRouter:
    """意图路由器 — 两层判断：关键词规则 + LLM语义分类"""

    KNOWLEDGE_KEYWORDS = [
        "政策", "规定", "制度", "文档", "规范", "流程",
        "怎么", "如何", "什么是", "解释", "说明",
        "policy", "rule", "document", "how to", "what is",
    ]

    SQL_KEYWORDS = [
        "查询", "统计", "报表", "销售额", "数据", "排名",
        "Top", "多少", "数量", "汇总", "平均",
        "query", "statistics", "report", "sales", "data", "top",
    ]

    TOOL_KEYWORDS = [
        "计算", "算一下", "搜索", "天气",
        "calculate", "search", "weather",
    ]

    def route(self, user_message: str) -> IntentResult:
        msg_lower = user_message.lower()

        # 第一层：关键词规则匹配（快速路径）
        for kw in self.KNOWLEDGE_KEYWORDS:
            if kw.lower() in msg_lower:
                return IntentResult(IntentType.KNOWLEDGE, 0.8)
        for kw in self.SQL_KEYWORDS:
            if kw.lower() in msg_lower:
                return IntentResult(IntentType.SQL_QUERY, 0.8)
        for kw in self.TOOL_KEYWORDS:
            if kw.lower() in msg_lower:
                return IntentResult(IntentType.TOOL_CALL, 0.8)

        # 默认：闲聊
        return IntentResult(IntentType.CHITCHAT, 0.5)


intent_router = IntentRouter()
