from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, JSON, DateTime, SmallInteger
from app.core.database import Base


class Workflow(Base):
    __tablename__ = "t_workflow"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    description = Column(Text)
    config = Column(JSON)
    status = Column(SmallInteger, nullable=False, default=1)
    version = Column(Integer, default=1)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, onupdate=datetime.now)
    is_deleted = Column(SmallInteger, nullable=False, default=0)
    creator_id = Column(BigInteger)


class WorkflowNode(Base):
    __tablename__ = "t_workflow_node"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id = Column(BigInteger, nullable=False, index=True)
    node_name = Column(String(128), nullable=False)
    node_type = Column(String(32), nullable=False)
    config = Column(JSON)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    create_time = Column(DateTime, nullable=False, default=datetime.now)


class WorkflowExecution(Base):
    __tablename__ = "t_workflow_execution"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id = Column(BigInteger, nullable=False, index=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    input_data = Column(JSON)
    output_data = Column(JSON)
    current_node = Column(String(128))
    error_msg = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    user_id = Column(BigInteger, index=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
