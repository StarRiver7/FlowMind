from fastapi import Request
from fastapi.responses import JSONResponse
from app.common.response.common import ErrorResponse
from app.common.exceptions.exceptions import AppException


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