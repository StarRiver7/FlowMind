
"""测试 SSE 事件格式。

验证:
  1. trace 事件格式正确
  2. token 事件格式正确
  3. done 事件格式正确
  4. 事件符合 SSE 规范
"""

import json
import pytest
from app.sse.chat_stream import StreamSender


class TestSSEEventFormat:
    """测试 SSE 事件格式。"""

    @pytest.mark.asyncio
    async def test_trace_event_format(self):
        """trace 事件符合 SSE 规范。"""
        event_str = await StreamSender.trace(
            step="intent_recognition",
            status="completed",
            step_order=1,
            detail={"intent": "sql"},
            duration_ms=150,
        )
        assert event_str.startswith("event: trace\n")
        assert "data:" in event_str

        # 解析 data
        lines = event_str.strip().split("\n")
        data_line = [l for l in lines if l.startswith("data:")][0]
        data = json.loads(data_line[5:].strip())
        assert data["step"] == "intent_recognition"
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_token_event_format(self):
        """token 事件格式。"""
        event_str = await StreamSender.token("你好")
        assert event_str.startswith("event: token\n")
        assert "你好" in event_str

    @pytest.mark.asyncio
    async def test_done_event_format(self):
        """done 事件格式。"""
        event_str = await StreamSender.done(
            intent="rag",
            sources=[{"document_name": "test.pdf"}],
            conversation_id="abc123",
        )
        assert event_str.startswith("event: done\n")
        data_line = [l for l in event_str.strip().split("\n") if l.startswith("data:")][0]
        data = json.loads(data_line[5:].strip())
        assert data["intent"] == "rag"
        assert data["conversation_id"] == "abc123"

    @pytest.mark.asyncio
    async def test_error_event_format(self):
        """error 事件格式。"""
        event_str = await StreamSender.error("测试错误", code="TEST")
        assert "event: error" in event_str

    @pytest.mark.asyncio
    async def test_multiple_events_concatenate(self):
        """多个事件可连续拼接。"""
        events = []
        events.append(await StreamSender.trace("step1", "running", step_order=1))
        events.append(await StreamSender.token("A"))
        events.append(await StreamSender.token("B"))
        events.append(await StreamSender.done(intent="chat"))

        combined = "".join(events)
        assert combined.count("event: trace") == 1
        assert combined.count("event: token") == 2
        assert combined.count("event: done") == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
