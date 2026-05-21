from typing import AsyncIterator, Literal
from src.config import settings
from src.utils.exceptions import LLMException
from .openai_client import OpenAIClient


class LLMGateway:
    """LLM Gateway — 统一管理多个Provider，支持模型切换、限流、重试"""

    def __init__(self):
        self._providers: dict[str, OpenAIClient] = {}
        self._init_providers()

    def _init_providers(self):
        if settings.openai_api_key:
            self._providers["openai"] = OpenAIClient()
        if settings.deepseek_api_key:
            from .openai_client import OpenAIClient as DSClient
            ds = DSClient()
            ds.client.base_url = settings.deepseek_base_url
            ds.client.api_key = settings.deepseek_api_key
            ds._model = settings.deepseek_model
            self._providers["deepseek"] = ds

    def _get_provider(self, model: str | None = None) -> OpenAIClient:
        if not self._providers:
            raise LLMException("No LLM provider configured")
        if model and model.startswith("deepseek"):
            return self._providers.get("deepseek", list(self._providers.values())[0])
        return self._providers.get("openai", list(self._providers.values())[0])

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        provider = self._get_provider(model)
        return await provider.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)

    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        provider = self._get_provider(model)
        async for token in provider.chat_stream(messages, model=model, temperature=temperature):
            yield token

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        provider = self._get_provider(model)
        return await provider.embed(texts)


# 全局单例
llm_gateway = LLMGateway()
