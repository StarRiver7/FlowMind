import time
import uuid
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.schemas.common import ErrorResponse
from src.utils.exceptions import AppException
from src.config import settings


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.trace_id = request_id
        request.state.start_time = time.time()

        response: Response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{time.time() - request.state.start_time:.3f}s"
        return response


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-Api-Key")
        if api_key != settings.java_service_api_key:
            return JSONResponse(
                status_code=401,
                content=ErrorResponse(
                    code=401,
                    message="Invalid API Key",
                    detail="X-Api-Key header is missing or invalid",
                ).model_dump(),
            )
        return await call_next(request)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code if 100 <= exc.code < 600 else 500,
        content=ErrorResponse(
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
        ).model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code=500,
            message="Internal server error",
            detail=str(exc),
        ).model_dump(),
    )
