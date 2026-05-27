"""Vector Repository — high-level repository bridging DB chunks and Milvus vectors.

Orchestrates the full index pipeline:
  1. Read chunks from t_document_chunk
  2. Embed with cache-aware batch processor
  3. Insert vectors into Milvus with metadata
  4. Update t_document_chunk.is_embedded and milvus_id
  5. Update t_document status
"""

import time
from typing import Optional
from sqlalchemy.orm import Session

from app.rag.embedding.embedding_service import embedding_service
from app.rag.vector_store.milvus_client import milvus_client
from app.rag.chunk.chunk_storage import chunk_storage
from app.kb.document_service import document_service
from app.kb.document_status import DocumentStatus
from app.kb.models import Document, KnowledgeSpace
from app.core.logger import get_logger

logger = get_logger(__name__)


class VectorRepository:
    """Repository for embedding → Milvus insert → status update."""

    async def index_document(
        self,
        db: Session,
        document_id: int,
        *,
        on_progress: Optional[callable] = None,
    ) -> dict:
        """Full index pipeline for a single document.

        Steps:
          1. Load document + space metadata
          2. Embed all chunks
          3. Insert into Milvus
          4. Update chunk embedding status
          5. Update document status

        Returns:
            {"success": bool, "document_id": int, "vector_count": int, ...}
        """
        start = time.time()

        # Load document and space
        doc = document_service.get_by_id(db, document_id)
        if not doc:
            return {"success": False, "error": "文档不存在"}

        space = db.query(KnowledgeSpace).filter(
            KnowledgeSpace.id == doc.space_id,
            KnowledgeSpace.is_deleted == 0,
        ).first()
        if not space:
            return {"success": False, "error": "知识空间不存在"}

        # Update status
        document_service.update_status(db, document_id, DocumentStatus.EMBEDDING)
        db.commit()

        # Embed
        embed_result = await embedding_service.embed_document(
            db, document_id, on_progress=on_progress,
        )
        if embed_result["chunk_count"] == 0:
            document_service.mark_failed(db, document_id, "无Chunk可Embedding")
            db.commit()
            return {"success": False, "error": "无Chunk可Embedding"}

        vectors = embed_result["vectors"]

        # Prepare metadata arrays
        chunk_ids = [cid for cid, _ in vectors]
        vec_list = [v for _, v in vectors]

        # Load chunk details for metadata
        chunks = chunk_storage.get_chunks_by_document(db, document_id, limit=10000)
        chunk_map = {c.id: c for c in chunks}

        contents = []
        token_counts = []
        page_numbers = []
        title_paths = []
        source_paths = []
        chunk_indices = []

        for cid in chunk_ids:
            c = chunk_map.get(cid)
            if c:
                contents.append(c.content)
                token_counts.append(c.char_count)  # chars ≈ tokens for now
                page_numbers.append(c.page_number or 0)
                title_paths.append("")
                source_paths.append(doc.file_path)
                chunk_indices.append(c.chunk_index)
            else:
                contents.append("")
                token_counts.append(0)
                page_numbers.append(0)
                title_paths.append("")
                source_paths.append(doc.file_path)
                chunk_indices.append(0)

        # Insert into Milvus
        milvus_ids = milvus_client.insert(
            vectors=vec_list,
            chunk_ids=chunk_ids,
            document_id=document_id,
            space_id=doc.space_id,
            department_id=space.department_id or 0,
            visibility=space.visibility,
            creator_id=doc.creator_id,
            contents=contents,
            token_counts=token_counts,
            page_numbers=page_numbers,
            title_paths=title_paths,
            source_paths=source_paths,
            chunk_indices=chunk_indices,
        )

        # Update chunk embedding status
        for i, (cid, mid) in enumerate(zip(chunk_ids, milvus_ids)):
            chunk_storage.update_embedding_status(
                db, document_id, chunk_map[cid].chunk_index, str(mid),
            )

        # Update document status
        document_service.update_status(
            db, document_id,
            new_status=DocumentStatus.INDEXED,
            chunk_count=len(vectors),
            token_count=sum(token_counts),
        )
        db.commit()

        elapsed = int((time.time() - start) * 1000)
        result = {
            "success": True,
            "document_id": document_id,
            "vector_count": len(vectors),
            "milvus_ids": milvus_ids,
            "elapsed_ms": elapsed,
        }

        logger.info(
            f"[VectorRepo] Indexed doc_id={document_id}: "
            f"{len(vectors)} vectors in {elapsed}ms"
        )
        return result

    async def delete_document(self, db: Session, document_id: int) -> int:
        """Delete all vectors and chunks for a document."""
        milvus_count = milvus_client.delete_by_document(document_id)
        chunk_storage.delete_chunks_by_document(db, document_id)
        return milvus_count

    def count_vectors(self) -> int:
        return milvus_client.count()


vector_repository = VectorRepository()
