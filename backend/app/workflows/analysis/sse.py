from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncGenerator

from app.core.workflow.types import Transition


class SseBroker:
    def __init__(self) -> None:
        self._channels: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)

    def _channel_key(self, workflow_id: str | None) -> str:
        return workflow_id or "__all__"

    async def publish(self, transition: Transition) -> None:
        payload = json.dumps(
            {
                "id": transition.workflow_id,
                "symbol": transition.symbol,
                "state": transition.state.value,
                "substate": transition.substate,
                "message": transition.message,
                "payload": transition.payload,
            }
        )
        targets = set(self._channels.get("__all__", set()))
        targets |= set(self._channels.get(transition.workflow_id, set()))
        for queue in targets:
            queue.put_nowait(payload)

    async def subscribe(self, workflow_id: str | None) -> AsyncGenerator[str, None]:
        key = self._channel_key(workflow_id)
        queue: asyncio.Queue[str] = asyncio.Queue()
        self._channels[key].add(queue)
        try:
            while True:
                event = await queue.get()
                yield f"data: {event}\n\n"
        finally:
            self._channels[key].discard(queue)


__all__ = ["SseBroker"]
