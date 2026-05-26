import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import setup_logging
from app.middleware.logging_middleware import RequestTracingMiddleware
from app.middleware.auth_middleware import ApiKeyMiddleware
from app.middleware.exception_middleware import app_exception_handler, general_exception_handler
from app.api.v1.chat_api import router as chat_router
from app.api.v1.rag_api import router as rag_router
from app.api.v1.health_api import router as health_router
from app.common.exceptions.exceptions import AppException

log_level = "DEBUG" if settings.debug else "INFO"
log_file = "logs/internsu-ai.log" if settings.env == "prod" else None
setup_logging(level=log_level, log_file=log_file)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"[InternSU AI] Starting in {settings.env} mode...")
    logger.info("  小SU 正在启动，准备帮老师们干活~")
    yield
    logger.info("[InternSU AI] 小SU 下班了~")


app = FastAPI(
    title="InternSU - 你的实习生同事 小su",
    version="1.0.0",
    description="企业内部 AI 实习生产品 - AI Engine",
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


def main():
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug, log_level="info")


if __name__ == "__main__":
    main()
