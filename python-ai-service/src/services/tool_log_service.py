from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from src.models.db import WriteSessionLocal
from src.models.tool_models import ToolCallLog


class ToolLogService:

    async def log(
        self,
        tool_name: str,
        tool_params: dict | None,
        tool_result: str | None,
        status: int,
        error_msg: str | None,
        execution_time_ms: int,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ):
        db: Session = WriteSessionLocal()
        try:
            log_entry = ToolCallLog(
                tool_name=tool_name,
                tool_params=tool_params,
                tool_result=tool_result,
                status=status,
                error_msg=error_msg,
                execution_time_ms=execution_time_ms,
                user_id=user_id,
                conversation_id=conversation_id,
                create_time=datetime.now(),
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def get_logs(
        self,
        user_id: int | None = None,
        tool_name: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        db: Session = WriteSessionLocal()
        try:
            stmt = select(ToolCallLog).order_by(desc(ToolCallLog.create_time))
            if user_id:
                stmt = stmt.where(ToolCallLog.user_id == user_id)
            if tool_name:
                stmt = stmt.where(ToolCallLog.tool_name == tool_name)
            stmt = stmt.limit(limit)

            results = db.execute(stmt).scalars().all()
            return [
                {
                    "id": r.id,
                    "tool_name": r.tool_name,
                    "status": r.status,
                    "execution_time_ms": r.execution_time_ms,
                    "error_msg": r.error_msg,
                    "create_time": r.create_time.isoformat() if r.create_time else None,
                }
                for r in results
            ]
        finally:
            db.close()


tool_log_service = ToolLogService()
