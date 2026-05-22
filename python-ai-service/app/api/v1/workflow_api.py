from datetime import datetime
from fastapi import APIRouter
from app.models.dto.workflow import WorkflowCreateRequest, WorkflowExecuteRequest
from app.services.workflow.workflow_service import workflow_service
from app.workflows.executors.workflow_engine import workflow_engine

router = APIRouter(prefix="/ai/workflow", tags=["Workflow"])


@router.get("")
async def list_workflows():
    return {"workflows": workflow_service.list_workflows()}


@router.post("")
async def create_workflow(req: WorkflowCreateRequest):
    result = workflow_service.create_workflow(
        name=req.name,
        description=req.description,
        config=req.config,
        creator_id=0,
    )
    return result


@router.post("/execute")
async def execute_workflow(req: WorkflowExecuteRequest):
    # 1. 创建执行记录
    exec_record = workflow_service.create_execution(
        workflow_id=req.workflow_id,
        input_data=req.input_data,
        user_id=req.user_id,
    )

    # 2. 标记为运行中
    workflow_service.update_execution(exec_record["id"], "running")
    execution_id = exec_record["id"]

    try:
        # 3. 执行工作流
        result = await workflow_engine.execute(
            workflow_config={"nodes": []},  # TODO: 从DB加载节点
            input_data=req.input_data,
        )

        if result.get("error"):
            workflow_service.update_execution(execution_id, "failed", error_msg=result["error"])
            return {"execution_id": execution_id, "status": "failed", "error": result["error"]}

        workflow_service.update_execution(execution_id, "completed", output_data=result)
        return {"execution_id": execution_id, "status": "completed", "output_data": result}

    except Exception as e:
        workflow_service.update_execution(execution_id, "failed", error_msg=str(e))
        return {"execution_id": execution_id, "status": "failed", "error": str(e)}


@router.get("/executions")
async def list_executions(workflow_id: int | None = None):
    return {"executions": workflow_service.get_executions(workflow_id=workflow_id)}
