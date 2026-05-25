from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class KBPermission:
    principal_type: str
    principal_id: str
    permission: str


class BaseKnowledgeManager(ABC):
    @abstractmethod
    def get_accessible_docs(self, user_id: str, tenant_id: str) -> list[str]:
        ...

    @abstractmethod
    async def search_authorized(self, query: str, user_id: str, tenant_id: str, *, kb_id: Optional[str] = None, top_k: int = 5) -> list[dict]:
        ...

    @abstractmethod
    def grant(self, doc_id: str, principal_type: str, principal_id: str, permission: str):
        ...

    @abstractmethod
    def revoke(self, doc_id: str, principal_type: str, principal_id: str):
        ...
