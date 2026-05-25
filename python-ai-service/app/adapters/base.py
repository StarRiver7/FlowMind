# ============================================================
# adapters/base.py — LLM Adapter Layer Abstract
# ============================================================
"""LLM Adapter Layer — defines the contract every model provider must fulfill.

Provides:
    - LLMResponse: structured response from any provider
    - BaseLLMAdapter: abstract interface for chat + stream + embed
    - ProviderType: enum for provider identification
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Optional, Any


class ProviderType(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class LLMResponse:
    """Unified response envelope from any LLM provider."""
    content: str
    model: str
    provider: ProviderType
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None
    tool_calls: Optional[list[dict]] = None


@dataclass
class ModelConfig:
    """Configuration for a single model instance."""
    provider: ProviderType
    model_name: str
    api_key: str
    base_url: str
    max_tokens: int = 4096
    temperature: float = 0.7
    priority: int = 0
    rate_limit_rpm: int = 60
    extra: dict = field(default_factory=dict)


class BaseLLMAdapter(ABC):
    """Abstract contract every LLM provider adapter must implement.

    Responsibilities:
        - chat(): synchronous completion
        - chat_stream(): streaming completion
        - embed(): text vectorization
        - Supports native function/tool calling via 'tools' kwarg
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request.

        Args:
            messages: OpenAI-format message list [{"role":"user","content":"..."}]
            model: Model name override (uses default if None)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum output tokens
            tools: Function definitions for native tool calling
            tool_choice: "auto", "none", or specific function name

        Returns:
            LLMResponse with content and optional tool_calls
        """
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat completion tokens via async generator."""
        ...

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        *,
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Convert texts to embedding vectors."""
        ...

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the enum type of this provider."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model name for this provider."""
        ...

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Estimate token count. Override for provider-specific tokenizers."""
        return len(text) // 4  # naive fallback
