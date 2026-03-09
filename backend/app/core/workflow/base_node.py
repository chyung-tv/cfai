from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any


class BaseNode(ABC):
    name: str = "base_node"
    timeout_seconds: float = 20.0
    max_retries: int = 0

    async def on_enter(self, context: dict[str, Any]) -> None:
        return None

    async def on_success(self, context: dict[str, Any], output: dict[str, Any]) -> None:
        return None

    async def on_error(self, context: dict[str, Any], error: Exception) -> None:
        return None

    async def on_exit(self, context: dict[str, Any]) -> None:
        return None

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        await self.on_enter(context)
        attempt = 0
        while True:
            try:
                output = await asyncio.wait_for(
                    self.run(context),
                    timeout=self.timeout_seconds,
                )
                await self.on_success(context, output)
                return output
            except Exception as exc:
                attempt += 1
                await self.on_error(context, exc)
                if attempt > self.max_retries:
                    raise
            finally:
                await self.on_exit(context)
