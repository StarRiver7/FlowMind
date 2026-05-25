from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, AsyncIterator


@dataclass
class SSEEvent:
    event: str = "message"
    data: str = ""
    id: Optional[str] = None
    retry: Optional[int] = None


class BaseStreamHandler(ABC):
    @abstractmethod
    async def publish(self, event: SSEEvent):
        ...

    @abstractmethod
    async def close(self):
        ...

    @abstractmethod
    def as_response(self, media_type: str = "text/event-stream"):
        ...
