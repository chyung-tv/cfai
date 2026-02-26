from __future__ import annotations

from app.workflow.base_node import BaseNode


class ResolveCacheNode(BaseNode):
    name = "resolve_cache"

    async def run(self, context: dict) -> dict:
        cached = context.get("cached_result")
        return {"cache_hit": cached is not None}
