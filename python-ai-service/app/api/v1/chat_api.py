
"""InternSU Chat API - SSE 流式聊天 + 工作过程推送。

POST /ai/chat       - 统一聊天接口 (stream=true 时 SSE)
GET  /ai/chat/stream - 流式聊天 (SSE)

SSE 事件类型:
  trace:  工作过程步骤 (右侧面板)
  token:  逐字输出 (消息气泡)
  meta:   元数据 (sources, tokens)
  done:   完成
  error:  错误
"""

import json
from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from app.models.dto.chat import ChatRequest
from app.graph.intern_graph import intern_graph
from app.memory.memory_manager import memory_manager
from app.sse.chat_stream import StreamSender
from app.common.response.common import ApiResponse
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Chat - 小SU"])


# ============================================================
# POST /ai/chat
# ============================================================

@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    """统一聊天接口。

    stream=true: 返回 SSE 流 (trace + token + meta + done 事件)
    stream=false: 返回完整 JSON 响应
    """
    if req.stream:
        return StreamingResponse(
            _sse_generator(req),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Type": "text/event-stream; charset=utf-8",
            },
        )

    # 非流式
    history = await memory_manager.get_history(req.user_id, req.conversation_id)
    restore_state = await memory_manager.restore_graph_state(req.user_id, req.conversation_id)
    result = await _run_graph(req, history, restore_state)
    await memory_manager.save_graph_state(req.user_id, req.conversation_id, result)
    final_text = result.get("final_answer", "")
    if not final_text:
        final_text = "收到老师～小SU遇到了问题，请查看服务器日志排查LLM连接"
    await memory_manager.record_turn(
        user_id=req.user_id, conv_id=req.conversation_id,
        user_msg=req.message, assistant_msg=final_text,
        sources=result.get("sources"), intent=result.get("intent", "chat"),
    )
    return ApiResponse(data={
        "content": final_text,
        "conversation_id": req.conversation_id,
        "intent": result.get("intent", "chat"),
        "sources": result.get("sources", []),
        "traces": result.get("trace_steps", []),
    }).model_dump()


# ============================================================
# POST /ai/chat/stream
# ============================================================

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """专用流式端点。"""
    req.stream = True
    return await chat(req, request)


# ============================================================
# SSE Generator
# ============================================================

async def _sse_generator(req: ChatRequest):
    """SSE 事件生成器。

    流程:
      1. 读取上下文记忆
      2. 执行 LangGraph
      3. 推送 trace 事件 (工作过程)
      4. 推送 meta 事件 (sources)
      5. 逐字推送 token 事件
      6. 推送 done 事件
      7. 持久化到 Redis + MySQL
    """
    sender = StreamSender()

    try:
        # Step 1: 读取上下文
        history = await memory_manager.get_history(req.user_id, req.conversation_id)
        yield await sender.trace("loading", "completed", step_order=0,
                                 detail={"history_rounds": len(history) // 2})

        # Step 1.5: restore agent state from Redis
        restore_state = await memory_manager.restore_graph_state(req.user_id, req.conversation_id)

        # Step 2: 执行 Graph (非流式获取完整结果)
        result = await _run_graph(req, history, restore_state)

        # Step 2.5: save agent state to Redis
        await memory_manager.save_graph_state(req.user_id, req.conversation_id, result)

        # Step 3: 推送 trace (工作过程)
        traces = result.get("trace_steps", [])
        for i, t in enumerate(traces):
            yield await sender.trace(
                step=t.get("node", ""),
                status=t.get("status", "completed"),
                step_order=i,
                detail=t.get("detail"),
                duration_ms=t.get("duration_ms"),
            )

        # Step 4: 推送 meta (sources)
        yield await sender.meta(
            sources=result.get("sources", []),
            tokens_used=result.get("tokens_used", 0),
            model_name=result.get("model_name", ""),
        )

        # Step 5: 逐字推送
        final_text = result.get("final_answer", "")
        if not final_text:
            final_text = "收到老师～小SU遇到了问题，请查看服务器日志排查LLM连接"
        for char in final_text:
            yield await sender.token(char)
        # Step 6: 完成
        yield await sender.done(
            intent=result.get("intent", "chat"),
            sources=result.get("sources", []),
            conversation_id=req.conversation_id,
        )

        # Step 7: 持久化
        await memory_manager.record_turn(
            user_id=req.user_id,
            conv_id=req.conversation_id,
            user_msg=req.message,
            assistant_msg=final_text,
            sources=result.get("sources"),
            intent=result.get("intent", "chat"),
        )

    except Exception as e:
        logger.error(f"SSE generator error: {e}")
        yield await sender.error(
            message="收到老师～我刚刚处理任务时遇到一点问题，请稍后再试～",
            code="INTERNAL_ERROR",
            detail={"error": str(e)},
        )
        yield await sender.done(
            intent="chat",
            sources=[],
            conversation_id=req.conversation_id,
        )


async def _run_graph(req, history=None, restore_state=None):
    """执行 LangGraph 并返回结果。"""
    result = await intern_graph.run(
        user_id=req.user_id,
        conversation_id=req.conversation_id,
        message=req.message,
        history=history,
        model_name=req.model or "deepseek-chat",
        restore_state=restore_state,
    )
    return result


# ============================================================
# Conversation management
# ============================================================

@router.get("/conversations")
async def list_conversations(user_id: str = Query(...)):
    convs = memory_manager.get_user_conversations(user_id)
    return ApiResponse(data={"conversations": convs, "total": len(convs)}).model_dump()


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, limit: int = Query(default=50, le=200)):
    messages = memory_manager.get_message_history(conversation_id, limit)
    return ApiResponse(data={"messages": messages, "total": len(messages)}).model_dump()


@router.post("/conversations")
async def create_conversation(
    user_id: str = Query(...),
    title: str = Query(default=""),
):
    conv_id = await memory_manager.start_conversation(user_id, title)
    return ApiResponse(data={"conversation_id": conv_id}).model_dump()
