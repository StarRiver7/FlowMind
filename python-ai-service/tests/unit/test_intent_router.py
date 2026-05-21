import pytest
from src.agent.router import IntentRouter, IntentType


class TestIntentRouter:
    def setup_method(self):
        self.router = IntentRouter()

    def test_route_knowledge_intent(self):
        result = self.router.route("公司年假政策是什么")
        assert result.intent == IntentType.KNOWLEDGE
        assert result.confidence > 0

    def test_route_sql_intent(self):
        result = self.router.route("查询上个月销售额Top10")
        assert result.intent == IntentType.SQL_QUERY

    def test_route_tool_intent(self):
        result = self.router.route("帮我计算 2+3*4")
        assert result.intent == IntentType.TOOL_CALL

    def test_route_chitchat_default(self):
        result = self.router.route("你好，今天过得怎么样")
        assert result.intent == IntentType.CHITCHAT

    def test_route_english_knowledge(self):
        result = self.router.route("What is the company policy on vacation?")
        assert result.intent == IntentType.KNOWLEDGE
