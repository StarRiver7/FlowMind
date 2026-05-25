from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional
from enum import Enum


class ProviderType(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"


@dataclass
class ModelConfig:
    provider: ProviderType
    model_name: str
    api_key: str
    base_url: str
    max_tokens: int = 4096
    temperature: float = 0.7
    priority: int = 0
    rate_limit_rpm: int = 60
    extra: dict = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: ProviderType
    usage: dict | None = None
    finish_reason: str | None = None


class BaseLLMProvider(ABC):

    @abstractmethod
    async def chat(
        self, messages: list[dict], model: str | None = None,
        temperature: float = 0.7, max_tokens: int = 4096, **kwargs,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def chat_stream(
        self, messages: list[dict], model: str | None = None,
        temperature: float = 0.7, **kwargs,
    ) -> AsyncIterator[str]:
        pass

    @abstractmethod
    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        pass

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        pass
