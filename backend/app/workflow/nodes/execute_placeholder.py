from __future__ import annotations

from datetime import datetime, timezone

from app.workflow.base_node import BaseNode


class ExecutePlaceholderNode(BaseNode):
    name = "assemble_result"

    async def run(self, context: dict) -> dict:
        symbol = context["symbol"]
        workflow_id = context["workflow_id"]
        now = datetime.now(timezone.utc).isoformat()
        result = {
            "id": workflow_id,
            "symbol": symbol,
            "price": 100.0,
            "score": 0,
            "tier": "Tier 2",
            "moat": "Narrow",
            "valuationStatus": "Fair",
            "thesis": {
                "executiveSummary": f"{symbol} baseline placeholder analysis.",
                "generatedAt": now,
            },
        }
        context["result"] = result
        return {"result": result}
