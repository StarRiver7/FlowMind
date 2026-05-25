from enum import Enum
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Enum as SAEnum
from app.core.database import Base


class PromptType(str, Enum):
    SYSTEM = "system"
    RAG = "rag"
    TOOL = "tool"
    SQL = "sql"


class PromptStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class PromptTemplate(Base):
    __tablename__ = "t_prompt_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, comment="模板名称")
    prompt_type = Column(SAEnum(PromptType), nullable=False, comment="类型")
    description = Column(String(512), comment="描述")
    system_template = Column(Text, nullable=False, comment="System Prompt Jinja2模板")
    user_template = Column(Text, default="""{{ user_message }}""", comment="User Message模板")
    variables_schema = Column(JSON, comment="变量JSON Schema定义")
    version = Column(Integer, default=1, comment="版本号")
    status = Column(SAEnum(PromptStatus), default=PromptStatus.DRAFT, comment="状态")
    provider_type = Column(String(32), comment="限定provider")
    model_name = Column(String(64), comment="限定模型")
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Integer, default=70)
    tags = Column(JSON, default=list, comment="标签")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, onupdate=datetime.now)
    is_deleted = Column(Integer, default=0)
    creator_id = Column(Integer, comment="创建者ID")


class PromptVariable(BaseModel):
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False
    default: Any = None


class PromptRenderInput(BaseModel):
    template_name: str
    variables: dict[str, Any] = Field(default_factory=dict)
    force_version: Optional[int] = None
