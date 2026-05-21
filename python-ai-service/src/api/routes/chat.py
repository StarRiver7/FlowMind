import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from src.schemas.chat import ChatRequest
from src.agent.executor import agent_executor

router = APIRouter(prefix="/ai", tags=["AI Chat"])


@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    """AI对话 — SSE流式返回"""
    if req.stream:

        async def event_stream():
            async for chunk in agent_executor.chat_stream(
                user_id=req.user_id,
                conversation_id=req.conversation_id,
                message=req.message,
                model=req.model,
                use_rag=req.use_rag,
                use_tools=req.use_tools,
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # 非流式
    result = await agent_executor.chat(
        user_id=req.user_id,
        conversation_id=req.conversation_id,
        message=req.message,
        model=req.model,
        use_rag=req.use_rag,
        use_tools=req.use_tools,
    )
    return result
