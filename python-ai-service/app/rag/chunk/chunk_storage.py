"""Chunk Storage — Chunk 入库 (t_document_chunk).

负责 Chunk 的批量写入、查询、删除。
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.kb.models import DocumentChunk
from app.rag.chunk.chunk_metadata import ChunkMetadata
from app.core.logger import get_logger

logger = get_logger(__name__)


class ChunkStorage:
    """Chunk 持久化层.

    写入 t_document_chunk 表，支持批量操作。
    """

    @staticmethod
    def save_chunks(
        db: Session,
        document_id: int,
        chunks: list[ChunkMetadata],
    ) -> int:
        """批量保存 Chunk 到数据库.

        Args:
            db: 数据库会话
            document_id: 所属文档 ID
            chunks: Chunk 元数据列表

        Returns:
            写入的 Chunk 数量
        """
        if not chunks:
            return 0

        records = []
        for meta in chunks:
            record = DocumentChunk(
                document_id=document_id,
                chunk_index=meta.chunk_index,
                content=meta.content,
                char_count=meta.char_count,
                page_number=meta.page_number,
                is_embedded=0,
                create_time=meta.created_time or datetime.now(),
            )
            records.append(record)

        db.add_all(records)
        db.commit()

        logger.info(
            f"[ChunkStorage] 入库完成: doc_id={document_id} "
            f"chunks={len(records)}"
        )
        return len(records)

    @staticmethod
    def get_chunks_by_document(
        db: Session,
        document_id: int,
        offset: int = 0,
        limit: int = 500,
    ) -> list[DocumentChunk]:
        """获取文档的所有 Chunk."""
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
        ).order_by(DocumentChunk.chunk_index).offset(offset).limit(limit).all()

    @staticmethod
    def get_chunk_count(db: Session, document_id: int) -> int:
        """获取文档的 Chunk 数量."""
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
        ).count()

    @staticmethod
    def delete_chunks_by_document(db: Session, document_id: int) -> int:
        """删除文档的所有 Chunk."""
        count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
        ).delete()
        db.commit()
        logger.info(f"[ChunkStorage] 删除 chunks: doc_id={document_id} count={count}")
        return count

    @staticmethod
    def update_embedding_status(
        db: Session,
        document_id: int,
        chunk_index: int,
        milvus_id: str,
    ) -> bool:
        """更新单个 Chunk 的向量化状态."""
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.chunk_index == chunk_index,
        ).first()
        if chunk:
            chunk.milvus_id = milvus_id
            chunk.is_embedded = 1
            db.commit()
            return True
        return False


# 模块单例
chunk_storage = ChunkStorage()
