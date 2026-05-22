from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, JSON, DateTime, SmallInteger
from app.core.database import Base


class ToolDefinition(Base):
    __tablename__ = "t_tool_definition"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    display_name = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    parameters_schema = Column(JSON, nullable=False)
    type = Column(String(32), nullable=False, default="builtin")
    executor_path = Column(String(512))
    is_require_confirm = Column(SmallInteger, default=0)
    timeout_seconds = Column(Integer, default=30)
    is_active = Column(SmallInteger, nullable=False, default=1)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, onupdate=datetime.now)
    is_deleted = Column(SmallInteger, nullable=False, default=0)
    creator_id = Column(BigInteger)


class ToolCallLog(Base):
    __tablename__ = "t_tool_call_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tool_name = Column(String(128), nullable=False, index=True)
    tool_params = Column(JSON)
    tool_result = Column(Text)
    status = Column(SmallInteger, nullable=False, default=1)
    error_msg = Column(String(1024))
    execution_time_ms = Column(Integer)
    user_id = Column(BigInteger, index=True)
    conversation_id = Column(BigInteger, index=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now, index=True)
