"""Conversation memory — Redis sliding window + MySQL persistence.

Dual-layer memory:
  Redis: hot sliding window for active conversations (fast, TTL-based)
  MySQL: cold storage for all messages (durable, queryable)
"""
import json
import uuid
from datetime import datetime
from typing import Optional
import redis.asyncio as aioredis
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import WriteSessionLocal
from app.core.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """Dual-layer conversation memory with sliding window."""

    PREFIX = "flowmind:session"
    CONV_LIST_KEY = "flowmind:conv_list"
    DEFAULT_TTL = 3600   # 1 hour for hot cache
    LONG_TTL = 86400 * 7  # 7 days for conversation list

    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._window = settings.conversation_window

    # ---- Redis connection ----

    async def _ensure_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
            )
        return self._redis

    def _key(self, user_id: str, conversation_id: str) -> str:
        return f"{self.PREFIX}:{user_id}:{conversation_id}"

    # ---- Hot cache: sliding window in Redis ----

    async def get_history(self, user_id: str, conversation_id: str) -> list[dict]:
        """Get sliding window of recent messages from Redis."""
        try:
            r = await self._ensure_redis()
            raw = await r.get(self._key(user_id, conversation_id))
            return json.loads(raw) if raw else []
        except Exception as e:
            logger.warning(f"Redis get history failed: {e}")
            return []

    async def add_message(self, user_id: str, conversation_id: str, role: str, content: str):
        """Add message to Redis sliding window."""
        try:
            r = await self._ensure_redis()
            key = self._key(user_id, conversation_id)
            history = await self.get_history(user_id, conversation_id)
            history.append({"role": role, "content": content})
            max_len = self._window * 2
            if len(history) > max_len:
                history = history[-max_len:]
            await r.setex(key, self.DEFAULT_TTL, json.dumps(history, ensure_ascii=False))
            # Also update conversation list timestamp
            await self._update_conv_list(user_id, conversation_id)
        except Exception as e:
            logger.warning(f"Redis add message failed: {e}")

    async def clear(self, user_id: str, conversation_id: str):
        """Remove conversation from Redis hot cache."""
        try:
            r = await self._ensure_redis()
            await r.delete(self._key(user_id, conversation_id))
        except Exception as e:
            logger.warning(f"Redis clear failed: {e}")

    # ---- Conversation list ----

    async def list_conversations(self, user_id: str) -> list[dict]:
        """List user's recent conversations from Redis cache."""
        try:
            r = await self._ensure_redis()
            raw = await r.hget(self.CONV_LIST_KEY, user_id)
            return json.loads(raw) if raw else []
        except Exception as e:
            logger.warning(f"Redis list conversations failed: {e}")
            return []

    async def _update_conv_list(self, user_id: str, conversation_id: str, title: str = ""):
        """Update conversation list entry in Redis."""
        try:
            r = await self._ensure_redis()
            raw = await r.hget(self.CONV_LIST_KEY, user_id)
            convs = json.loads(raw) if raw else []
            now = datetime.now().isoformat()
            # Upsert
            found = False
            for c in convs:
                if c["conversation_id"] == conversation_id:
                    c["title"] = title or c["title"]
                    c["updated_at"] = now
                    found = True
                    break
            if not found:
                convs.insert(0, {
                    "conversation_id": conversation_id,
                    "title": title or "New Conversation",
                    "created_at": now,
                    "updated_at": now,
                })
            # Keep last 50
            convs = convs[:50]
            await r.hset(self.CONV_LIST_KEY, user_id, json.dumps(convs, ensure_ascii=False))
            await r.expire(self.CONV_LIST_KEY, self.LONG_TTL)
        except Exception as e:
            logger.warning(f"Redis update conv list failed: {e}")

    # ---- Cold storage: MySQL persistence ----

    def _persist_message(
        self, user_id: str, conversation_id: str, role: str,
        content: str, sources: list | None = None, intent: str | None = None,
    ):
        """Persist message to MySQL (synchronous, called via thread)."""
        from app.models.entity.chat_models import ChatMessage, Conversation
        db: Session = WriteSessionLocal()
        try:
            # Upsert conversation
            conv = db.query(Conversation).filter(
                Conversation.conversation_id == conversation_id,
                Conversation.is_deleted == 0,
            ).first()
            if not conv:
                conv = Conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    title="",
                    model=settings.deepseek_default_model,
                    message_count=0,
                )
                db.add(conv)
                db.flush()

            # Insert message
            msg = ChatMessage(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                content=content,
                sources=json.dumps(sources, ensure_ascii=False) if sources else None,
                intent=intent,
                token_count=len(content) // 4,  # rough estimate
            )
            db.add(msg)

            # Update conversation counter
            conv.message_count = (conv.message_count or 0) + 1
            conv.update_time = datetime.now()
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"MySQL persist message failed: {e}")
        finally:
            db.close()

    def persist_user_message(self, user_id: str, conversation_id: str, content: str):
        """Persist user message to MySQL."""
        self._persist_message(user_id, conversation_id, "user", content)

    def persist_assistant_message(
        self, user_id: str, conversation_id: str, content: str,
        sources: list | None = None, intent: str | None = None,
    ):
        """Persist assistant message with optional sources to MySQL."""
        self._persist_message(user_id, conversation_id, "assistant", content, sources, intent)

    def get_message_history(self, conversation_id: str, limit: int = 50) -> list[dict]:
        """Load full message history from MySQL."""
        from app.models.entity.chat_models import ChatMessage
        db: Session = WriteSessionLocal()
        try:
            msgs = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.is_deleted == 0,
            ).order_by(ChatMessage.create_time.asc()).limit(limit).all()
            return [
                {"role": m.role, "content": m.content, "sources": m.sources, "intent": m.intent}
                for m in msgs
            ]
        except Exception as e:
            logger.warning(f"MySQL get history failed: {e}")
            return []
        finally:
            db.close()

    def get_user_conversations(self, user_id: str, limit: int = 20) -> list[dict]:
        """List user's conversations from MySQL."""
        from app.models.entity.chat_models import Conversation
        db: Session = WriteSessionLocal()
        try:
            convs = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.is_deleted == 0,
            ).order_by(Conversation.update_time.desc()).limit(limit).all()
            return [
                {
                    "conversation_id": c.conversation_id,
                    "title": c.title or "New Conversation",
                    "model": c.model,
                    "message_count": c.message_count,
                    "created_at": c.create_time.isoformat() if c.create_time else None,
                    "updated_at": c.update_time.isoformat() if c.update_time else None,
                }
                for c in convs
            ]
        except Exception as e:
            logger.warning(f"MySQL list conversations failed: {e}")
            return []
        finally:
            db.close()

    # ---- Full session workflow ----

    def generate_conversation_id(self) -> str:
        """Generate a new UUID-based conversation ID."""
        return uuid.uuid4().hex[:16]

    async def start_conversation(self, user_id: str, title: str = "") -> str:
        """Start a new conversation, returns conversation_id."""
        conv_id = self.generate_conversation_id()
        await self._update_conv_list(user_id, conv_id, title)
        return conv_id

    async def record_turn(
        self, user_id: str, conversation_id: str, user_msg: str,
        assistant_msg: str, sources: list | None = None, intent: str | None = None,
    ):
        """Record a complete chat turn to both Redis and MySQL."""
        # Redis hot cache
        await self.add_message(user_id, conversation_id, "user", user_msg)
        await self.add_message(user_id, conversation_id, "assistant", assistant_msg)
        # Redis conv list
        await self._update_conv_list(user_id, conversation_id)
        # MySQL cold storage
        self.persist_user_message(user_id, conversation_id, user_msg)
        self.persist_assistant_message(user_id, conversation_id, assistant_msg, sources, intent)


memory_manager = MemoryManager()