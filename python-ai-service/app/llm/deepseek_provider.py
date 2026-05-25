from typing import AsyncIterator
from openai import AsyncOpenAI
from app.core.config import settings
from app.llm.base import BaseLLMProvider, LLMResponse, ProviderType


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek Provider - deepseek-chat (V3), deepseek-reasoner (R1)"""

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self._default_model = settings.deepseek_default_model

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.DEEPSEEK

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
            provider=ProviderType.DEEPSEEK,
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
        raise NotImplementedError("DeepSeek does not provide embedding API")
