"""Workflow API - stub for future workflow engine."""
from fastapi import APIRouter
from app.models.dto.workflow import WorkflowCreateRequest, WorkflowExecuteRequest

router = APIRouter(prefix="/ai/workflow", tags=["Workflow"])


@router.get("")
async def list_workflows():
    return {"workflows": []}


@router.post("")
async def create_workflow(req: WorkflowCreateRequest):
    return {"status": "not_implemented", "message": "Workflow engine coming soon"}


@router.post("/execute")
async def execute_workflow(req: WorkflowExecuteRequest):
    return {"status": "not_implemented", "message": "Workflow engine coming soon"}


@router.get("/executions")
async def list_executions(workflow_id: int | None = None):
    return {"executions": []}