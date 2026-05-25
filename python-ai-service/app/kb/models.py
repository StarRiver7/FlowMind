from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from app.core.database import Base


class KnowledgeBase(Base):
    __tablename__ = "t_knowledge_base"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(String(512))
    tenant_id = Column(String(64), nullable=False)
    embedding_model = Column(String(64), default="text-embedding-3-small")
    chunk_size = Column(Integer, default=512)
    chunk_overlap = Column(Integer, default=64)
    status = Column(Integer, default=1)
    config = Column(JSON)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, onupdate=datetime.now)
    is_deleted = Column(Integer, default=0)
    creator_id = Column(Integer)


class DocumentPermission(Base):
    __tablename__ = "t_document_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, nullable=False)
    principal_type = Column(String(32), nullable=False)
    principal_id = Column(String(64), nullable=False)
    permission = Column(String(16), default="read")
    create_time = Column(DateTime, default=datetime.now)
    creator_id = Column(Integer)
