from pydantic import BaseModel, Field
from typing import Optional


class WorkflowCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=2000)
    config: dict = Field(default_factory=dict)


class WorkflowExecuteRequest(BaseModel):
    workflow_id: int
    input_data: dict = Field(default_factory=dict)
    user_id: Optional[int] = None


class WorkflowExecutionResponse(BaseModel):
    execution_id: int
    status: str
    output_data: Optional[dict] = None
    error_msg: Optional[str] = None
