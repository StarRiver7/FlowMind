from fastapi import APIRouter
from app.tools.tool_registry import tool_registry
from app.services.tool.tool_log_service import tool_log_service
from app.models.dto.tool import ToolExecuteRequest, ToolExecuteResponse, ToolLogQuery

router = APIRouter(prefix="/ai/tools", tags=["Tools"])


@router.get("")
async def list_tools():
    """列出所有可用工具"""
    return {"tools": tool_registry.list_tools()}


@router.get("/definitions")
async def get_definitions():
    """获取LLM function calling格式的工具定义"""
    return {"tools": tool_registry.get_all_definitions()}


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute(req: ToolExecuteRequest):
    """执行工具调用 — 含超时控制、参数校验、日志记录"""
    result = await tool_registry.execute(
        name=req.tool_name,
        user_id=req.user_id,
        conversation_id=req.conversation_id,
        **req.params,
    )
    return ToolExecuteResponse(
        success=result["success"],
        result=result.get("result"),
        error=result.get("error"),
        execution_time_ms=result.get("execution_time_ms", 0),
    )


@router.get("/logs")
async def get_logs(user_id: int | None = None, tool_name: str | None = None, limit: int = 50):
    """查询工具调用日志"""
    logs = tool_log_service.get_logs(user_id=user_id, tool_name=tool_name, limit=limit)
    return {"total": len(logs), "logs": logs}
