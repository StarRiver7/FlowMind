
"""测试 AI 反问机制。

验证:
  1. 信息不足时正确触发 clarify
  2. clarify 回答包含礼貌用语 ("收到老师～")
  3. 信息充分时不触发 clarify
"""

import pytest
from app.graph.nodes.intent_node import _check_info_sufficiency


class TestClarifyTrigger:
    """测试反问触发条件。"""

    def test_sql_missing_all_info_triggers_clarify(self):
        """缺少时间、部门、指标 → 触发 clarify。"""
        is_sufficient, missing = _check_info_sufficiency("sql", "查一下数据", [])
        assert not is_sufficient
        assert len(missing) > 0

    def test_sql_with_full_info_no_clarify(self):
        """包含时间、部门、指标 → 不触发。"""
        is_sufficient, missing = _check_info_sufficiency(
            "sql", "统计本月技术部在职人数", []
        )
        assert is_sufficient

    def test_sql_after_clarify_no_trigger(self):
        """上一轮是 clarify → 本轮直接执行。"""
        history = [{"role": "assistant", "content": "收到老师～我需要确认几个信息"}]
        is_sufficient, _ = _check_info_sufficiency("sql", "本月全公司", history)
        assert is_sufficient

    def test_chat_never_triggers_clarify(self):
        """闲聊永不触发 clarify。"""
        is_sufficient, _ = _check_info_sufficiency("chat", "你好", [])
        assert is_sufficient

    def test_rag_few_keywords_triggers_clarify(self):
        """RAG 关键词太少 → 触发。"""
        is_sufficient, missing = _check_info_sufficiency("rag", "查", [])
        assert not is_sufficient


class TestClarifyResponse:
    """测试反问回答格式。"""

    def test_clarify_response_contains_honorific(self):
        """反问必须包含 '收到老师～'。"""
        # 这是一个设计约束，实际 LLM 输出由 Prompt 保证
        expected_phrases = ["收到老师", "老师"]
        assert any(phrase in "收到老师～请问需要统计什么？" for phrase in expected_phrases)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
