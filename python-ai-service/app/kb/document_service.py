"""Document Service — 文档 CRUD + 状态管理.

管理 t_document 表的增删改查及状态流转。
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.kb.models import Document, KnowledgeSpace
from app.kb.document_status import DocumentStatus, can_transition, next_status, is_terminal
from app.core.logger import get_logger

logger = get_logger(__name__)


class DocumentService:
    """文档服务层.

    提供文档的 CRUD 及状态流转管理。
    """

    # ---- 创建 ----

    @staticmethod
    def create(
        db: Session,
        space_id: int,
        file_name: str,
        file_type: str,
        file_size: int,
        file_path: str,
        file_hash: str,
        creator_id: int,
    ) -> Document:
        """创建文档记录（初始状态: uploaded）."""
        doc = Document(
            space_id=space_id,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type.lstrip("."),
            file_path=file_path,
            file_hash=file_hash,
            processing_status=DocumentStatus.UPLOADED,
            chunk_count=0,
            token_count=0,
            creator_id=creator_id,
            create_time=datetime.now(),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 更新知识空间文档计数
        DocumentService._increment_space_doc_count(db, space_id)

        logger.info(
            f"[Doc] 文档记录创建 id={doc.id} name='{file_name}' "
            f"type={file_type} size={file_size} space={space_id}"
        )
        return doc

    # ---- 查询 ----

    @staticmethod
    def get_by_id(db: Session, doc_id: int) -> Optional[Document]:
        """根据ID获取文档."""
        return db.query(Document).filter(
            Document.id == doc_id,
            Document.is_deleted == 0,
        ).first()

    @staticmethod
    def list_by_space(
        db: Session,
        space_id: int,
        offset: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
    ) -> tuple[list[Document], int]:
        """列出知识空间下的文档."""
        q = db.query(Document).filter(
            Document.space_id == space_id,
            Document.is_deleted == 0,
        )
        if status_filter:
            q = q.filter(Document.processing_status == status_filter)

        total = q.count()
        items = q.order_by(Document.create_time.desc()).offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def list_by_user(
        db: Session,
        creator_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Document], int]:
        """列出用户上传的所有文档."""
        q = db.query(Document).filter(
            Document.creator_id == creator_id,
            Document.is_deleted == 0,
        )
        total = q.count()
        items = q.order_by(Document.create_time.desc()).offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def find_by_hash(db: Session, file_hash: str, space_id: int) -> Optional[Document]:
        """按哈希查找（去重检测）."""
        return db.query(Document).filter(
            Document.file_hash == file_hash,
            Document.space_id == space_id,
            Document.is_deleted == 0,
        ).first()

    # ---- 状态流转 ----

    @staticmethod
    def update_status(
        db: Session,
        doc_id: int,
        new_status: str,
        error_msg: Optional[str] = None,
        chunk_count: Optional[int] = None,
        token_count: Optional[int] = None,
    ) -> Optional[Document]:
        """更新文档状态（带流转校验）."""
        doc = DocumentService.get_by_id(db, doc_id)
        if not doc:
            return None

        # 终态不可再更新（除非是 FAILED → 重新处理）
        if is_terminal(doc.processing_status) and doc.processing_status != DocumentStatus.FAILED:
            logger.warning(f"[Doc] 文档 id={doc_id} 已是终态 '{doc.processing_status}'，拒绝更新为 '{new_status}'")
            return doc

        if not can_transition(doc.processing_status, new_status):
            logger.warning(
                f"[Doc] 文档 id={doc_id} 不允许从 '{doc.processing_status}' 转到 '{new_status}'"
            )
            return doc

        old_status = doc.processing_status
        doc.processing_status = new_status

        if error_msg is not None:
            doc.error_msg = error_msg
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if token_count is not None:
            doc.token_count = token_count

        doc.update_time = datetime.now()
        db.commit()
        db.refresh(doc)

        logger.info(f"[Doc] 状态流转 id={doc_id} '{old_status}' → '{new_status}'")
        return doc

    @staticmethod
    def mark_failed(db: Session, doc_id: int, error_msg: str) -> Optional[Document]:
        """将文档标记为失败."""
        return DocumentService.update_status(
            db, doc_id,
            new_status=DocumentStatus.FAILED,
            error_msg=error_msg,
        )

    @staticmethod
    def advance_status(db: Session, doc_id: int) -> Optional[Document]:
        """自动前进到下一个状态."""
        doc = DocumentService.get_by_id(db, doc_id)
        if not doc:
            return None
        nxt = next_status(doc.processing_status)
        if nxt is None:
            return doc
        return DocumentService.update_status(db, doc_id, new_status=nxt)

    # ---- 删除 ----

    @staticmethod
    def soft_delete(db: Session, doc_id: int) -> bool:
        """软删除文档."""
        doc = DocumentService.get_by_id(db, doc_id)
        if not doc:
            return False

        doc.is_deleted = 1
        db.commit()

        # 更新知识空间文档计数
        DocumentService._decrement_space_doc_count(db, doc.space_id)

        logger.info(f"[Doc] 文档已删除 id={doc_id} name='{doc.file_name}'")
        return True

    # ---- 内部辅助 ----

    @staticmethod
    def _increment_space_doc_count(db: Session, space_id: int) -> None:
        space = db.query(KnowledgeSpace).filter(KnowledgeSpace.id == space_id).first()
        if space:
            space.document_count = (space.document_count or 0) + 1
            db.commit()

    @staticmethod
    def _decrement_space_doc_count(db: Session, space_id: int) -> None:
        space = db.query(KnowledgeSpace).filter(KnowledgeSpace.id == space_id).first()
        if space:
            space.document_count = max(0, (space.document_count or 0) - 1)
            db.commit()


# 模块单例
document_service = DocumentService()
