from datetime import datetime
from sqlalchemy.orm import Session
from src.models.db import WriteSessionLocal
from src.models.workflow_models import Workflow, WorkflowNode, WorkflowExecution


class WorkflowService:

    def create_workflow(self, name: str, description: str, config: dict, creator_id: int) -> dict:
        db: Session = WriteSessionLocal()
        try:
            wf = Workflow(
                name=name,
                description=description,
                config=config,
                status=1,
                version=1,
                creator_id=creator_id,
                create_time=datetime.now(),
            )
            db.add(wf)
            db.commit()
            db.refresh(wf)
            return {"id": wf.id, "name": wf.name}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def list_workflows(self) -> list[dict]:
        db: Session = WriteSessionLocal()
        try:
            wfs = db.query(Workflow).filter(Workflow.is_deleted == 0).all()
            return [{"id": w.id, "name": w.name, "status": w.status, "version": w.version} for w in wfs]
        finally:
            db.close()

    def create_execution(self, workflow_id: int, input_data: dict, user_id: int | None = None) -> dict:
        db: Session = WriteSessionLocal()
        try:
            exec_entry = WorkflowExecution(
                workflow_id=workflow_id,
                status="pending",
                input_data=input_data,
                user_id=user_id,
                create_time=datetime.now(),
            )
            db.add(exec_entry)
            db.commit()
            db.refresh(exec_entry)
            return {"id": exec_entry.id, "status": exec_entry.status}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def update_execution(self, execution_id: int, status: str, output_data: dict | None = None, error_msg: str | None = None):
        db: Session = WriteSessionLocal()
        try:
            exec_entry = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
            if exec_entry:
                exec_entry.status = status
                if output_data:
                    exec_entry.output_data = output_data
                if error_msg:
                    exec_entry.error_msg = error_msg
                if status == "completed":
                    exec_entry.completed_at = datetime.now()
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def get_executions(self, workflow_id: int | None = None, limit: int = 20) -> list[dict]:
        db: Session = WriteSessionLocal()
        try:
            q = db.query(WorkflowExecution).order_by(WorkflowExecution.create_time.desc())
            if workflow_id:
                q = q.filter(WorkflowExecution.workflow_id == workflow_id)
            results = q.limit(limit).all()
            return [
                {
                    "id": e.id,
                    "workflow_id": e.workflow_id,
                    "status": e.status,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "error_msg": e.error_msg,
                }
                for e in results
            ]
        finally:
            db.close()


workflow_service = WorkflowService()
