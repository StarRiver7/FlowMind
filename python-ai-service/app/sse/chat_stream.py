
"""InternSU SSE 流式处理器。

统一管理 SSE 事件发送，支持:
  - trace: 工作过程追踪事件
  - token: 逐字输出事件
  - meta: 元数据事件 (sources, tokens)
  - error: 错误事件
  - done: 完成事件
  - heartbeat: 心跳保活
"""

import json
import time


class StreamSender:
    """SSE 事件发送器。

    生成符合 SSE 规范的格式化事件字符串。
    """

    @staticmethod
    async def trace(
        step: str,
        status: str,  # running, completed, failed
        step_order: int = 0,
        detail: dict | None = None,
        duration_ms: int | None = None,
    ) -> str:
        """发送工作过程追踪事件。

        对应前端"实习生工作过程"右侧面板的每一步。
        """
        data = {
            "step": step,
            "status": status,
            "step_order": step_order,
        }
        if detail:
            data["detail"] = detail
        if duration_ms is not None:
            data["duration_ms"] = duration_ms
        if status == "running":
            data["started_at"] = _iso_now()

        return _sse_event("trace", data)

    @staticmethod
    async def token(content: str) -> str:
        """发送单个 token。

        对应前端消息气泡的逐字追加。
        """
        return _sse_event("token", {"content": content})

    @staticmethod
    async def meta(sources: list | None = None, tokens_used: int = 0, model_name: str = "") -> str:
        """发送元数据。

        在 token 流结束前或结束后发送 Source 引用和 Token 统计。
        """
        return _sse_event("meta", {
            "sources": sources or [],
            "tokens_used": tokens_used,
            "model_name": model_name,
        })

    @staticmethod
    async def error(message: str, code: str = "UNKNOWN", detail: dict | None = None) -> str:
        """发送错误事件。"""
        data = {"code": code, "message": message}
        if detail:
            data["detail"] = detail
        return _sse_event("error", data)

    @staticmethod
    async def done(intent: str = "chat", sources: list | None = None,
                   conversation_id: str = "") -> str:
        """发送完成事件。"""
        return _sse_event("done", {
            "intent": intent,
            "sources": sources or [],
            "conversation_id": conversation_id,
        })

    @staticmethod
    async def heartbeat() -> str:
        """发送心跳保活。"""
        return _sse_event("heartbeat", {"ts": int(time.time())})

    # ---- 向后兼容别名 ----
    @staticmethod
    async def thinking(content: str) -> str:
        """向后兼容的 thinking 事件，映射为 trace 事件。"""
        return _sse_event("trace", {
            "step": "thinking",
            "status": "running",
            "detail": {"content": content},
        })


class InternSSEHandler:
    """InternSU SSE 事件流处理器。

    将 LangGraph 的 InternState 增量转换为 SSE 事件流。
    """

    @staticmethod
    async def stream_traces(traces: list[dict]) -> list[str]:
        """将 traces 列表转为 SSE 事件列表。"""
        events = []
        for t in traces:
            events.append(await StreamSender.trace(
                step=t.get("step", ""),
                status=t.get("status", "completed"),
                step_order=t.get("step_order", 0),
                detail=t.get("detail"),
                duration_ms=t.get("duration_ms"),
            ))
        return events

    @staticmethod
    async def stream_response(
        response: str,
        intent: str = "chat",
        sources: list | None = None,
        tokens_used: int = 0,
        model_name: str = "",
        conversation_id: str = "",
    ) -> list[str]:
        """将最终回答转为完整 SSE 事件流。

        Returns:
            包括 meta、token (逐字)、done 事件。
        """
        events = []

        # 先发 meta
        events.append(await StreamSender.meta(
            sources=sources or [],
            tokens_used=tokens_used,
            model_name=model_name,
        ))

        # 逐 token 发送
        for char in response:
            events.append(await StreamSender.token(char))

        # 完成
        events.append(await StreamSender.done(
            intent=intent,
            sources=sources or [],
            conversation_id=conversation_id,
        ))

        return events


def _sse_event(event: str, data: dict) -> str:
    """构建 SSE 格式的事件字符串。"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _iso_now() -> str:
    """当前时间的 ISO 字符串。"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
