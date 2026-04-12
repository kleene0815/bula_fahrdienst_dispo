"""Einfacher In-Memory SSE-Broadcaster für die Disponenten-Ansicht."""
import asyncio
import json
from collections.abc import AsyncGenerator


class EventBroadcaster:
    def __init__(self) -> None:
        self._queues: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        try:
            self._queues.remove(q)
        except ValueError:
            pass

    async def broadcast(self, event: str, data: dict) -> None:
        payload = json.dumps(data, default=str)
        for q in list(self._queues):
            await q.put({"event": event, "data": payload})

    async def stream(self, q: asyncio.Queue) -> AsyncGenerator[str, None]:
        """Async-Generator für FastAPI StreamingResponse."""
        try:
            while True:
                msg = await q.get()
                yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self.unsubscribe(q)


broadcaster = EventBroadcaster()
