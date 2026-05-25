from fastapi import APIRouter
from app.tools.registry import tool_registry
from app.models.dto.tool import ToolExecuteRequest, ToolExecuteResponse

router = APIRouter(prefix="/ai/tools", tags=["Tools"])


@router.get("")
async def list_tools():
    return {"tools": tool_registry.list_tools()}


@router.get("/definitions")
async def get_definitions():
    return {"tools": tool_registry.get_all_definitions()}


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute(req: ToolExecuteRequest):
    result = await tool_registry.execute(req.tool_name, **req.params)
    return ToolExecuteResponse(
        success=result["success"],
        result=result.get("result"),
        error=result.get("error"),
        execution_time_ms=result.get("execution_time_ms", 0),
    )


@router.get("/logs")
async def get_logs(user_id: int | None = None, tool_name: str | None = None, limit: int = 50):
    return {"total": 0, "logs": [], "note": "Tool logging to be integrated with DB"}
