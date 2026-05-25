"""SSE Stream Handler — concrete implementation for Server-Sent Events."""
import json
import asyncio
from typing import AsyncIterator, Optional
from fastapi.responses import StreamingResponse
from app.streaming.base import SSEEvent, BaseStreamHandler
from app.core.logger import get_logger

logger = get_logger(__name__)


class SSEStreamHandler(BaseStreamHandler):
    """Concrete SSE handler wrapping an async generator into StreamingResponse.

    Usage:
        handler = SSEStreamHandler()
        async def my_generator():
            await handler.send(content="Hello", event="token")
            await handler.send(content="World", event="token")
            await handler.done(sources=[...])
        return handler.as_response(my_generator())
    """

    def __init__(self, heartbeat_interval: float = 15.0):
        self._heartbeat = heartbeat_interval
        self._closed = False

    async def publish(self, event: SSEEvent):
        """Publish a raw SSEEvent (implemented via yield in generator)."""
        pass  # This method is a placeholder; actual sending uses send()/done()

    async def close(self):
        self._closed = True

    @staticmethod
    def _format_sse(event: str = "message", data: str = "", event_id: Optional[str] = None) -> str:
        """Format a single SSE message."""
        lines = []
        if event_id:
            lines.append(f"id: {event_id}")
        if event and event != "message":
            lines.append(f"event: {event}")
        for line in data.split("\n"):
            lines.append(f"data: {line}")
        lines.append("")  # blank line terminates
        return "\n".join(lines)

    def as_response(
        self,
        generator,
        media_type: str = "text/event-stream",
    ) -> StreamingResponse:
        """Wrap generator into a StreamingResponse with proper headers."""
        return StreamingResponse(
            generator,
            media_type=media_type,
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Type": "text/event-stream; charset=utf-8",
            },
        )


class StreamSender:
    """Utility for sending typed SSE events from within a generator.

    Usage inside an async generator:
        sender = StreamSender()
        await sender.token("Hello")
        await sender.token(" world")
        await sender.done(intent="chat", sources=[...])
    """

    def __init__(self, heartbeat_interval: float = 15.0):
        self._seq = 0
        self._heartbeat = heartbeat_interval

    def _next_id(self) -> str:
        self._seq += 1
        return str(self._seq)

    async def token(self, text: str) -> str:
        """Send a content token chunk."""
        payload = json.dumps({"type": "token", "content": text}, ensure_ascii=False)
        return SSEStreamHandler._format_sse(event="token", data=payload, event_id=self._next_id())

    async def thinking(self, message: str) -> str:
        """Send a thinking/status message."""
        payload = json.dumps({"type": "thinking", "content": message}, ensure_ascii=False)
        return SSEStreamHandler._format_sse(event="status", data=payload, event_id=self._next_id())

    async def error(self, message: str) -> str:
        """Send an error event."""
        payload = json.dumps({"type": "error", "content": message}, ensure_ascii=False)
        return SSEStreamHandler._format_sse(event="error", data=payload)

    async def done(
        self,
        intent: str = "chat",
        sources: list | None = None,
        conversation_id: str = "",
    ) -> str:
        """Send the final done event with metadata."""
        payload = json.dumps({
            "type": "done",
            "intent": intent,
            "sources": sources or [],
            "conversation_id": conversation_id,
        }, ensure_ascii=False)
        return SSEStreamHandler._format_sse(event="done", data=payload)

    async def heartbeat(self) -> str:
        """Send a keep-alive heartbeat comment."""
        return ": heartbeat\n\n"