from typing import AsyncIterator
from openai import AsyncOpenAI
from app.core.config import settings
from app.llm.base import BaseLLMProvider, LLMResponse, ProviderType


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider - GPT-4o, GPT-4o-mini, text-embedding-3-small"""

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._default_model = settings.openai_default_model

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI

    @property
    def default_model(self) -> str:
        return self._default_model

    async def chat(
        self, messages: list[dict], model: str | None = None,
        temperature: float = 0.7, max_tokens: int = 4096, **kwargs,
    ) -> LLMResponse:
        model = model or self._default_model
        resp = await self._client.chat.completions.create(
            model=model, messages=messages,
            temperature=temperature, max_tokens=max_tokens, **kwargs,
        )
        choice = resp.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider=ProviderType.OPENAI,
            usage=resp.usage.model_dump() if resp.usage else None,
            finish_reason=choice.finish_reason,
        )

    async def chat_stream(
        self, messages: list[dict], model: str | None = None,
        temperature: float = 0.7, **kwargs,
    ) -> AsyncIterator[str]:
        model = model or self._default_model
        stream = await self._client.chat.completions.create(
            model=model, messages=messages,
            temperature=temperature, stream=True, **kwargs,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        model = model or settings.embedding_model
        resp = await self._client.embeddings.create(model=model, input=texts)
        return [d.embedding for d in resp.data]
