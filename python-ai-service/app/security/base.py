from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthContext:
    user_id: str
    username: str
    roles: list[str]
    tenant_id: str = "default"
    permissions: list[str] = None


class BaseAuthenticator(ABC):
    @abstractmethod
    async def authenticate(self, token: str) -> AuthContext:
        ...

    @abstractmethod
    async def validate_permission(self, ctx: AuthContext, resource: str, action: str) -> bool:
        ...
