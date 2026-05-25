"""Knowledge Base Manager — tenant isolation + document ACL."""
from sqlalchemy.orm import Session
from app.core.database import WriteSessionLocal
from app.kb.models import KnowledgeBase, DocumentPermission
from app.pipeline.rag_pipeline import rag_pipeline
from app.core.logger import get_logger

logger = get_logger(__name__)


class KBManager:
    """Knowledge base tenant isolation with document-level ACL."""

    def get_accessible_docs(self, user_id: int, tenant_id: str) -> list[int]:
        """Get list of document IDs the user has access to."""
        db: Session = WriteSessionLocal()
        try:
            perms = db.query(DocumentPermission).filter(
                DocumentPermission.principal_type == "user",
                DocumentPermission.principal_id == str(user_id),
            ).all()
            return list(set(p.document_id for p in perms))
        finally:
            db.close()

    async def search_authorized(
        self, query: str, user_id: int, tenant_id: str,
        kb_id: int | None = None, top_k: int = 5,
    ) -> list[dict]:
        """Search knowledge base with ACL filtering."""
        accessible_docs = self.get_accessible_docs(user_id, tenant_id)

        return await rag_pipeline.search(
            query=query,
            top_k=top_k,
            use_rerank=True,
            with_citation=True,
            doc_ids=[str(d) for d in accessible_docs] if accessible_docs else None,
            tenant_id=tenant_id,
        )

    def grant_permission(
        self, document_id: int, principal_type: str,
        principal_id: str, permission: str = "read", creator_id: int = 0,
    ):
        db: Session = WriteSessionLocal()
        try:
            perm = DocumentPermission(
                document_id=document_id,
                principal_type=principal_type,
                principal_id=principal_id,
                permission=permission,
                creator_id=creator_id,
            )
            db.add(perm)
            db.commit()
            logger.info(f"Granted {permission} on doc {document_id} to {principal_type}:{principal_id}")
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def revoke_permission(self, document_id: int, principal_type: str, principal_id: str):
        db: Session = WriteSessionLocal()
        try:
            db.query(DocumentPermission).filter(
                DocumentPermission.document_id == document_id,
                DocumentPermission.principal_type == principal_type,
                DocumentPermission.principal_id == principal_id,
            ).delete()
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


kb_manager = KBManager()
