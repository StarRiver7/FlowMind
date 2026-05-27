"""Knowledge Base Service — 知识空间 CRUD + 权限隔离.

支持三种 visibility 级别:
  - private:  仅创建者可见
  - department: 同部门成员可见
  - public:   全员可见

权限隔离规则由查询时的 user_id + department_id 共同决定。
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.kb.models import KnowledgeSpace
from app.schemas.kb_schemas import CreateKnowledgeBaseRequest, KnowledgeBaseResponse
from app.core.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseService:
    """知识空间服务层.

    提供知识空间的 CRUD，内置权限隔离逻辑。
    """

    @staticmethod
    def create(
        db: Session,
        req: CreateKnowledgeBaseRequest,
        creator_id: int,
    ) -> KnowledgeSpace:
        """创建知识空间.

        Raises:
            ValueError: 参数校验不通过
        """
        if req.visibility == "department" and req.department_id is None:
            raise ValueError("部门级可见的知识空间必须指定 department_id")

        space = KnowledgeSpace(
            name=req.name,
            description=req.description,
            visibility=req.visibility,
            department_id=req.department_id,
            creator_id=creator_id,
            embedding_model=req.embedding_model,
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
            status=1,
            create_time=datetime.now(),
        )
        db.add(space)
        db.commit()
        db.refresh(space)

        logger.info(
            f"[KB] 知识空间创建成功 id={space.id} name='{space.name}' "
            f"visibility={space.visibility} creator={creator_id}"
        )
        return space

    @staticmethod
    def list_for_user(
        db: Session,
        user_id: int,
        department_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[KnowledgeSpace], int]:
        """列出用户有权限访问的知识空间.

        权限规则:
          1. 用户自己创建的 (creator_id = user_id)
          2. visibility = 'public'
          3. visibility = 'department' 且 department_id 匹配
        """
        base_filter = and_(
            KnowledgeSpace.is_deleted == 0,
            KnowledgeSpace.status == 1,
        )

        permission_filter = or_(
            KnowledgeSpace.creator_id == user_id,
            KnowledgeSpace.visibility == "public",
            and_(
                KnowledgeSpace.visibility == "department",
                KnowledgeSpace.department_id == department_id,
            ),
        )

        query = db.query(KnowledgeSpace).filter(base_filter, permission_filter)

        total = query.count()
        items = query.order_by(KnowledgeSpace.create_time.desc()).offset(offset).limit(limit).all()

        return items, total

    @staticmethod
    def get_by_id(db: Session, space_id: int, user_id: int, department_id: Optional[int] = None) -> Optional[KnowledgeSpace]:
        """获取知识空间（带权限校验）."""
        space = db.query(KnowledgeSpace).filter(
            KnowledgeSpace.id == space_id,
            KnowledgeSpace.is_deleted == 0,
        ).first()

        if not space:
            return None

        # 权限校验
        if not KnowledgeBaseService._can_access(space, user_id, department_id):
            return None

        return space

    @staticmethod
    def update(
        db: Session,
        space_id: int,
        user_id: int,
        department_id: Optional[int] = None,
        **kwargs,
    ) -> Optional[KnowledgeSpace]:
        """更新知识空间（仅创建者可操作）."""
        space = KnowledgeBaseService.get_by_id(db, space_id, user_id, department_id)
        if not space:
            return None
        if space.creator_id != user_id:
            return None

        allowed = {"name", "description", "visibility", "department_id", "embedding_model", "chunk_size", "chunk_overlap", "status"}
        for key, value in kwargs.items():
            if key in allowed and value is not None:
                setattr(space, key, value)

        db.commit()
        db.refresh(space)
        return space

    @staticmethod
    def delete(db: Session, space_id: int, user_id: int, department_id: Optional[int] = None) -> bool:
        """软删除知识空间（仅创建者可操作）."""
        space = KnowledgeBaseService.get_by_id(db, space_id, user_id, department_id)
        if not space or space.creator_id != user_id:
            return False

        space.is_deleted = 1
        db.commit()
        logger.info(f"[KB] 知识空间已删除 id={space_id}")
        return True

    @staticmethod
    def _can_access(space: KnowledgeSpace, user_id: int, department_id: Optional[int]) -> bool:
        """判断用户是否有权限访问该知识空间."""
        if space.creator_id == user_id:
            return True
        if space.visibility == "public":
            return True
        if space.visibility == "department" and space.department_id == department_id:
            return True
        return False


# 模块单例
knowledge_base_service = KnowledgeBaseService()
