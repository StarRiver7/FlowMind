"""Chat API — streaming chat, conversation management, message history."""
import json
from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from app.models.dto.chat import ChatRequest, ChatMessage
from app.agents.agent_executor import agent_executor
from app.streaming.sse_handler import StreamSender
from app.common.response.common import ApiResponse
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Chat"])


# ============================================================
# POST /ai/chat — non-streaming + SSE streaming in one endpoint
# ============================================================

@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    """Unified chat endpoint.

    When stream=false: returns complete JSON response.
    When stream=true: returns SSE stream with token events.
    """
    if req.stream:
        return StreamingResponse(
            _sse_event_generator(req),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Type": "text/event-stream; charset=utf-8",
            },
        )

    # Non-streaming
    result = await agent_executor.chat(
        user_id=req.user_id,
        conversation_id=req.conversation_id,
        message=req.message,
        use_rag=req.use_rag,
        use_tools=req.use_tools,
    )
    return ApiResponse(data=result).model_dump()


async def _sse_event_generator(req: ChatRequest):
    """SSE event generator wrapping the stream orchestrator."""
    sender = StreamSender()
    seq = 0

    try:
        async for event in agent_executor.chat_stream(
            user_id=req.user_id,
            conversation_id=req.conversation_id,
            message=req.message,
            use_rag=req.use_rag,
            use_tools=req.use_tools,
            model=req.model,
        ):
            seq += 1
            etype = event.get("type", "token")
            content = event.get("content", "")

            if etype == "thinking":
                yield await sender.thinking(content)
            elif etype == "token":
                yield await sender.token(content)
            elif etype == "error":
                yield await sender.error(content)
            elif etype == "done":
                yield await sender.done(
                    intent=event.get("intent", "chat"),
                    sources=event.get("sources", []),
                    conversation_id=event.get("conversation_id", req.conversation_id),
                )
            # Heartbeat every 30 events
            if seq % 30 == 0:
                yield await sender.heartbeat()

    except Exception as e:
        logger.error(f"SSE generator error: {e}")
        yield await sender.error(str(e))
        yield await sender.done(intent="chat", sources=[], conversation_id=req.conversation_id)


# ============================================================
# POST /ai/chat/stream — dedicated streaming endpoint
# ============================================================

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """Dedicated streaming endpoint. Always returns SSE."""
    req.stream = True
    return await chat(req, request)


# ============================================================
# Conversation management
# ============================================================

@router.get("/chat/conversations")
async def list_conversations(
    user_id: str = Query(..., description="User ID"),
):
    """List all conversations for a user."""
    convs = agent_executor.get_conversations(user_id)
    return ApiResponse(data={"conversations": convs, "total": len(convs)}).model_dump()


@router.get("/chat/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = Query(default=50, le=200),
):
    """Get message history for a conversation."""
    messages = agent_executor.get_history(conversation_id, limit)
    return ApiResponse(data={"messages": messages, "total": len(messages)}).model_dump()


@router.post("/chat/conversations")
async def create_conversation(
    user_id: str = Query(..., description="User ID"),
    title: str = Query(default="", description="Optional conversation title"),
):
    """Create a new conversation and return its ID."""
    conv_id = await agent_executor.start_conversation(user_id, title)
    return ApiResponse(data={"conversation_id": conv_id}).model_dump()