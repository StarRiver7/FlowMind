from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/ai", tags=["Health"])


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai-agent-python-service",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health/llm")
async def health_llm():
    try:
        from app.llm.gateway import llm_gateway
        resp = await llm_gateway.chat([{"role": "user", "content": "hi"}], max_tokens=10)
        return {"llm": "ok", "model": str(resp.model), "response": resp.content[:50]}
    except Exception as e:
        return {"llm": "error", "detail": str(e)}
