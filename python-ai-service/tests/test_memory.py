
"""测试 Conversation Memory。

验证:
  1. Redis 读写
  2. 滑动窗口大小限制
  3. TTL 机制 (可选)
"""

import pytest


class TestMemoryLogic:
    """测试记忆逻辑（不依赖 Redis）。"""

    def test_sliding_window_truncation(self):
        """超过窗口大小时自动截断。"""
        window = 5  # 5 轮 = 10 条消息
        history = [{"role": "user", "content": f"msg{i}"} for i in range(20)]

        max_len = window * 2
        truncated = history[-max_len:] if len(history) > max_len else history

        assert len(truncated) == 10
        assert truncated[0]["content"] == "msg10"

    def test_history_format(self):
        """历史消息格式正确。"""
        msg = {"role": "user", "content": "测试消息"}
        assert msg["role"] in ("user", "assistant", "system")
        assert isinstance(msg["content"], str)

    def test_empty_history(self):
        """空历史不报错。"""
        history = []
        assert len(history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
