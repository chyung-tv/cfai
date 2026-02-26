from __future__ import annotations

from app.workflow.base_node import BaseNode


class ValidateInputNode(BaseNode):
    name = "validate_input"

    async def run(self, context: dict) -> dict:
        symbol = str(context.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError("symbol is required")
        context["symbol"] = symbol
        return {"symbol": symbol}
