from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        pass

    @abstractmethod
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        pass

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass
