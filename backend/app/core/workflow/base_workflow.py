from __future__ import annotations

from typing import Any

from app.core.workflow.base_node import BaseNode


class BaseWorkflowRunner:
    async def run_node(self, node: BaseNode, context: dict[str, Any]) -> dict[str, Any]:
        return await node.execute(context)
