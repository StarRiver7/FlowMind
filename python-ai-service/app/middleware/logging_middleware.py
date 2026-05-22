import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.trace_id = request_id
        request.state.start_time = time.time()

        response: Response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{time.time() - request.state.start_time:.3f}s"
        return response