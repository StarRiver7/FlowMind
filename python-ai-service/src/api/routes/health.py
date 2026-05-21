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
