from __future__ import annotations

from datetime import datetime, timezone

from app.providers.gemini_deep_research import (
    DeepResearchProviderError,
    GeminiDeepResearchClient,
)
from app.workflow.base_node import BaseNode
from app.workflow.prompts.deep_research_prompt import build_deep_research_prompt


class DeepResearchNode(BaseNode):
    name = "deep_research"
    timeout_seconds = 60.0 * 30

    def __init__(self, client: GeminiDeepResearchClient) -> None:
        self._client = client

    async def run(self, context: dict) -> dict:
        symbol = str(context.get("symbol", "")).strip().upper()
        workflow_id = str(context.get("workflow_id", "")).strip()
        company_name = context.get("catalog_name_display")

        if not symbol:
            raise ValueError("symbol is required")
        if not workflow_id:
            raise ValueError("workflow_id is required")

        prompt = build_deep_research_prompt(
            symbol=symbol,
            company_name=company_name,
        )

        try:
            provider_result = await self._client.run_report(prompt=prompt)
        except DeepResearchProviderError as exc:
            raise RuntimeError(f"{exc.code}: {exc}") from exc

        generated_at = datetime.now(timezone.utc).isoformat()
        citations = [
            {
                "title": item.title,
                "url": item.url,
                "publisher": item.publisher,
                "accessedAt": item.accessed_at,
            }
            for item in provider_result.citations
        ]

        result = {
            "id": workflow_id,
            "symbol": symbol,
            "reportMarkdown": provider_result.report_markdown,
            "citations": citations,
            "interactionId": provider_result.interaction_id,
            "generatedAt": generated_at,
            "modelMetadata": provider_result.model_metadata,
        }
        context["deep_research_interaction_id"] = provider_result.interaction_id
        context["report_markdown"] = provider_result.report_markdown
        context["report_citations"] = citations
        context["report_generated_at"] = generated_at
        context["model_metadata"] = provider_result.model_metadata
        context["result"] = result
        return {"result": result}
