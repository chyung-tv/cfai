from __future__ import annotations

from app.core.workflow.base_node import BaseNode
from app.workflows.analysis.context import WorkflowContext


class PublishSseNode(BaseNode):
    name = "publish_sse"

    async def run(self, context: WorkflowContext) -> dict:
        # SSE is emitted by orchestrator transitions; this node marks pipeline completion.
        return {"published": True}


__all__ = ["PublishSseNode"]
