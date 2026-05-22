import json
from typing import Any
import redis.asyncio as aioredis
from app.core.config import settings


class MemoryManager:
    """对话记忆管理器 — Redis短期记忆 + 滑动窗口"""

    SESSION_PREFIX = "session"
    SUMMARY_PREFIX = "summary"
    DEFAULT_TTL = 1800  # 30分钟

    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._window_size = settings.conversation_window

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}",
                password=settings.redis_password,
                decode_responses=True,
            )
        return self._redis

    def _key(self, user_id: str, conversation_id: str) -> str:
        return f"{self.SESSION_PREFIX}:{user_id}:{conversation_id}"

    async def get_history(self, user_id: str, conversation_id: str) -> list[dict]:
        """获取对话历史 — 最近N轮"""
        try:
            r = await self._get_redis()
            raw = await r.get(self._key(user_id, conversation_id))
            if raw:
                return json.loads(raw)
        except Exception:
            pass
        return []

    async def add_message(
        self, user_id: str, conversation_id: str, role: str, content: str
    ):
        """添加消息到历史 — 超出窗口自动截断"""
        try:
            r = await self._get_redis()
            key = self._key(user_id, conversation_id)
            history = await self.get_history(user_id, conversation_id)
            history.append({"role": role, "content": content})

            # 滑动窗口截断 — 保留最近N*2条消息（N轮=N个user+N个assistant）
            max_len = self._window_size * 2
            if len(history) > max_len:
                history = history[-max_len:]

            await r.setex(key, self.DEFAULT_TTL, json.dumps(history, ensure_ascii=False))
        except Exception:
            pass

    async def clear(self, user_id: str, conversation_id: str):
        """清除对话历史"""
        try:
            r = await self._get_redis()
            await r.delete(self._key(user_id, conversation_id))
        except Exception:
            pass


memory_manager = MemoryManager()
