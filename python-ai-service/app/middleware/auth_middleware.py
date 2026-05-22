from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.common.response.common import ErrorResponse
from app.core.config import settings


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