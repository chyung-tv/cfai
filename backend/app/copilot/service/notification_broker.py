from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class NotificationBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, *, user_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._subscribers[user_id].add(queue)
        return queue

    async def unsubscribe(self, *, user_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(user_id)
            if not subscribers:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(user_id, None)

    async def publish(self, *, user_id: str, event: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.get(user_id, set()))
        for queue in subscribers:
            try:
                queue.put_nowait({"event": event, "payload": payload})
            except asyncio.QueueFull:
                continue
