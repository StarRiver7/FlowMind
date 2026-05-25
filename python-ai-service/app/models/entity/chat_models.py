"""Chat persistence models — conversations and messages stored in MySQL."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from app.core.database import Base


class Conversation(Base):
    """Long-term conversation storage."""
    __tablename__ = "t_conversation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), nullable=False, unique=True, comment="UUID conversation ID")
    user_id = Column(String(64), nullable=False, comment="Owner user ID")
    title = Column(String(256), default="New Conversation", comment="Auto-generated or user-set title")
    model = Column(String(64), default="deepseek-chat", comment="LLM model used")
    message_count = Column(Integer, default=0, comment="Total message count")
    status = Column(Integer, default=1, comment="1=active, 0=archived")
    metadata_ = Column("metadata", JSON, default=dict)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_conv_user", "user_id", "status"),
        Index("idx_conv_id", "conversation_id"),
    )


class ChatMessage(Base):
    """Individual chat message stored in MySQL."""
    __tablename__ = "t_chat_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), nullable=False, comment="FK to t_conversation.conversation_id")
    user_id = Column(String(64), nullable=False, comment="Message author user ID")
    role = Column(String(16), nullable=False, comment="user / assistant / system / tool")
    content = Column(Text, nullable=False, comment="Message text content")
    token_count = Column(Integer, default=0, comment="Token count for this message")
    sources = Column(JSON, default=None, comment="RAG source citations if any")
    intent = Column(String(32), default=None, comment="Classified intent: chat/rag/tool/sql")
    metadata_ = Column("metadata", JSON, default=dict)
    create_time = Column(DateTime, default=datetime.now)
    is_deleted = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_msg_conv", "conversation_id", "create_time"),
        Index("idx_msg_user", "user_id", "create_time"),
    )