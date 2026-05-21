import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.utils.logging_config import setup_logging
from src.api.middleware import (
    RequestTracingMiddleware,
    ApiKeyMiddleware,
    app_exception_handler,
    general_exception_handler,
)
from src.api.routes.chat import router as chat_router
from src.api.routes.rag import router as rag_router
from src.api.routes.health import router as health_router
from src.api.routes.tool import router as tool_router
from src.api.routes.workflow import router as workflow_router
from src.utils.exceptions import AppException

# 初始化日志
log_level = "DEBUG" if settings.debug else "INFO"
log_file = "logs/python-ai-service.log" if settings.env == "prod" else None
setup_logging(level=log_level, log_file=log_file)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"[{settings.app_name}] Starting in {settings.env} mode...")
    yield
    logger.info(f"[{settings.app_name}] Shutting down...")


app = FastAPI(
    title="Enterprise AI Agent - Python AI Service",
    version="1.0.0",
    description="Agent-RAG-Tool-Workflow",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(RequestTracingMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(health_router)
app.include_router(tool_router)
app.include_router(workflow_router)


def main():
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=settings.debug, log_level="info")


if __name__ == "__main__":
    main()
