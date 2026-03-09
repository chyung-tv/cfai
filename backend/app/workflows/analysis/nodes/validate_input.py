from __future__ import annotations

from app.core.workflow.base_node import BaseNode
from app.workflows.analysis.context import WorkflowContext


class ValidateInputNode(BaseNode):
    name = "validate_input"

    async def run(self, context: WorkflowContext) -> dict:
        symbol = str(context.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError("symbol is required")
        context["symbol"] = symbol
        return {"symbol": symbol}


__all__ = ["ValidateInputNode"]
