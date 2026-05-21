from openai import AsyncOpenAI
from typing import AsyncIterator, Any
from src.config import settings
from .base import BaseLLMProvider


class OpenAIClient(BaseLLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._model = settings.openai_model

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(self, messages: list[dict], **kwargs) -> str:
        model = kwargs.pop("model", self._model)
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=kwargs.pop("temperature", 0.7),
            max_tokens=kwargs.pop("max_tokens", 4096),
            **kwargs,
        )
        return response.choices[0].message.content or ""

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        model = kwargs.pop("model", self._model)
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=kwargs.pop("temperature", 0.7),
            max_tokens=kwargs.pop("max_tokens", 4096),
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in response.data]
