# ============================================================
# adapters/factory.py — Adapter Factory
# ============================================================
"""Provider-agnostic adapter factory.

Creates and caches LLM adapters. Supports runtime registration
of custom providers. Gateway-level concerns (retry, fallback,
rate limiting) belong in the gateway, not here.
"""

from typing import Optional
from app.adapters.base import BaseLLMAdapter, ProviderType


class AdapterFactory:
    """Factory for creating and caching LLM adapter instances.

    Usage:
        factory = AdapterFactory()
        adapter = factory.create(ProviderType.OPENAI, api_key="...")
        response = await adapter.chat([{"role":"user","content":"hello"}])
    """

    def __init__(self):
        self._adapters: dict[ProviderType, BaseLLMAdapter] = {}
        self._creators: dict[ProviderType, type[BaseLLMAdapter]] = {}

    def register(self, provider_type: ProviderType, adapter_cls: type[BaseLLMAdapter]):
        """Register a new adapter class for a provider type."""
        self._creators[provider_type] = adapter_cls

    def create(self, provider_type: ProviderType, **config) -> BaseLLMAdapter:
        """Create or retrieve a cached adapter instance."""
        if provider_type in self._adapters:
            return self._adapters[provider_type]

        if provider_type not in self._creators:
            raise ValueError(f"No adapter registered for provider: {provider_type}")

        adapter = self._creators[provider_type](**config)
        self._adapters[provider_type] = adapter
        return adapter

    @property
    def available_providers(self) -> list[ProviderType]:
        return list(self._creators.keys())


adapter_factory = AdapterFactory()
