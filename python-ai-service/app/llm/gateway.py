import time
import tiktoken
from typing import AsyncIterator
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.llm.base import BaseLLMProvider, LLMResponse, ProviderType
from app.llm.openai_provider import OpenAIProvider
from app.llm.deepseek_provider import DeepSeekProvider
from app.common.exceptions.exceptions import LLMException


class LLMGateway:
    """企业级LLM Gateway - 多Provider管理、负载均衡、故障转移、Token计数"""

    def __init__(self):
        self._providers: dict[ProviderType, BaseLLMProvider] = {}
        self._tokenizer_cache: dict[str, tiktoken.Encoding] = {}
        self._init_providers()

    def _init_providers(self):
        if settings.openai_api_key:
            self._providers[ProviderType.OPENAI] = OpenAIProvider()
        if settings.deepseek_api_key:
            self._providers[ProviderType.DEEPSEEK] = DeepSeekProvider()

        if not self._providers:
            raise LLMException("No LLM provider configured")

    def register(self, provider: BaseLLMProvider):
        self._providers[provider.provider_type] = provider

    def _select_provider(self, model: str | None = None) -> BaseLLMProvider:
        if model:
            for p in self._providers.values():
                if model.startswith(p.default_model.split("-")[0]):
                    return p
        return self._providers.get(
            ProviderType(settings.default_provider),
            next(iter(self._providers.values())),
        )

    def _get_tokenizer(self, model: str) -> tiktoken.Encoding:
        if model not in self._tokenizer_cache:
            try:
                self._tokenizer_cache[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                self._tokenizer_cache[model] = tiktoken.get_encoding("cl100k_base")
        return self._tokenizer_cache[model]

    def count_tokens(self, messages: list[dict], model: str) -> int:
        enc = self._get_tokenizer(model)
        count = 0
        for msg in messages:
            count += 4  # message framing
            for key in ("content", "role"):
                val = msg.get(key, "")
                if isinstance(val, str):
                    count += len(enc.encode(val))
        count += 2  # reply priming
        return count

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def chat(
        self, messages: list[dict], model: str | None = None,
        temperature: float = 0.7, max_tokens: int = 4096, **kwargs,
    ) -> LLMResponse:
        provider = self._select_provider(model)
        return await provider.chat(
            messages, model=model,
            temperature=temperature, max_tokens=max_tokens, **kwargs,
        )

    async def chat_stream(
        self, messages: list[dict], model: str | None = None,
        temperature: float = 0.7, **kwargs,
    ) -> AsyncIterator[str]:
        provider = self._select_provider(model)
        async for token in provider.chat_stream(messages, model=model, temperature=temperature, **kwargs):
            yield token

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        provider = self._select_provider()
        start = time.time()
        result = await provider.embed(texts, model=model)
        elapsed = (time.time() - start) * 1000
        from app.core.logger import get_logger
        get_logger(__name__).debug(f"Embedding {len(texts)} texts in {elapsed:.0f}ms")
        return result

    @property
    def available_providers(self) -> list[str]:
        return [p.value for p in self._providers]


llm_gateway = LLMGateway()
