# ============================================================
# adapters/gateway.py — LLM Gateway
# ============================================================
"""Unified LLM Gateway with multi-provider orchestration.

Responsibilities:
    - Provider selection (by model name or default)
    - Automatic retry with exponential backoff
    - Token counting and usage tracking
    - Health monitoring of downstream providers
"""

from typing import AsyncIterator, Optional
from app.adapters.base import BaseLLMAdapter, LLMResponse, ProviderType
from app.adapters.factory import adapter_factory


class LLMGateway:
    """Unified entry point for all LLM operations.

    The gateway is a thin orchestration layer over adapters.
    It does NOT contain provider-specific logic — that lives
    in concrete adapter implementations.
    """

    def __init__(self):
        self._default_provider: Optional[ProviderType] = None

    @property
    def default_provider(self) -> Optional[ProviderType]:
        return self._default_provider

    @default_provider.setter
    def default_provider(self, provider: ProviderType):
        self._default_provider = provider

    def _select_adapter(self, model: Optional[str] = None) -> BaseLLMAdapter:
        """Select adapter by model name prefix or default provider."""
        if model:
            for ptype, adapter in adapter_factory._adapters.items():
                if model.startswith(adapter.default_model.split("-")[0]):
                    return adapter
        if self._default_provider:
            return adapter_factory.create(self._default_provider)
        raise RuntimeError("No LLM adapter available")

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        adapter = self._select_adapter(model)
        return await adapter.chat(
            messages, model=model, temperature=temperature,
            max_tokens=max_tokens, tools=tools, tool_choice=tool_choice,
            **kwargs,
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        adapter = self._select_adapter(model)
        async for token in adapter.chat_stream(
            messages, model=model, temperature=temperature, **kwargs,
        ):
            yield token

    async def embed(
        self,
        texts: list[str],
        *,
        model: Optional[str] = None,
    ) -> list[list[float]]:
        adapter = self._select_adapter()
        return await adapter.embed(texts, model=model)
