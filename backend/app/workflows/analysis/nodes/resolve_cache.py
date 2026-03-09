from __future__ import annotations

from app.core.workflow.base_node import BaseNode
from app.workflows.analysis.context import WorkflowContext


class ResolveCacheNode(BaseNode):
    name = "resolve_cache"

    async def run(self, context: WorkflowContext) -> dict:
        cached = context.get("cached_result")
        return {"cache_hit": cached is not None}


__all__ = ["ResolveCacheNode"]
