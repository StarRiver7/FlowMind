from abc import ABC, abstractmethod


class BaseMemory(ABC):
    @abstractmethod
    async def get_history(self, user_id: str, conversation_id: str) -> list[dict]:
        ...

    @abstractmethod
    async def add_message(self, user_id: str, conversation_id: str, role: str, content: str):
        ...

    @abstractmethod
    async def clear(self, user_id: str, conversation_id: str):
        ...

    @abstractmethod
    async def get_conversations(self, user_id: str) -> list[dict]:
        ...
