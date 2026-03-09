from __future__ import annotations

from pydantic import ValidationError

from app.core.workflow.base_node import BaseNode
from app.providers.gemini_deep_research import (
    DeepResearchProviderError,
    GeminiDeepResearchClient,
)
from app.workflows.analysis.context import WorkflowContext
from app.workflows.analysis.prompts.structured_output_prompt import (
    build_structured_output_prompt,
)
from app.workflows.analysis.schemas.structured_output import StructuredOutputModel


class StructuredOutputNode(BaseNode):
    name = "structured_output"
    timeout_seconds = 60.0 * 5

    def __init__(self, client: GeminiDeepResearchClient) -> None:
        self._client = client

    async def run(self, context: WorkflowContext) -> dict:
        result = context.get("result")
        if not isinstance(result, dict):
            raise ValueError("deep research result is missing")

        report_markdown = result.get("reportMarkdown")
        if not isinstance(report_markdown, str) or not report_markdown.strip():
            raise ValueError("reportMarkdown is required for structured output")

        try:
            raw = await self._client.generate_json_object(
                prompt=build_structured_output_prompt(
                    report_markdown=report_markdown,
                )
            )
        except DeepResearchProviderError as exc:
            raise RuntimeError(f"structured_output_{exc.code}: {exc}") from exc

        try:
            structured_output_model = StructuredOutputModel.model_validate(raw)
        except ValidationError as exc:
            raise RuntimeError(f"structured_output_validation_failed: {exc}") from exc
        structured_output = structured_output_model.model_dump(mode="json")
        result["structuredOutput"] = structured_output

        model_metadata = result.get("modelMetadata")
        if isinstance(model_metadata, dict):
            model_metadata["structuredOutput"] = {
                "mode": "fixed_llm",
                "model": self._client.structured_output_model_name,
                "schemaVersion": structured_output.get("schemaVersion"),
            }
        else:
            result["modelMetadata"] = {
                "structuredOutput": {
                    "mode": "fixed_llm",
                    "model": self._client.structured_output_model_name,
                    "schemaVersion": structured_output.get("schemaVersion"),
                }
            }

        context["structured_output"] = structured_output
        context["result"] = result
        return {"result": result, "structuredOutput": structured_output}


__all__ = ["StructuredOutputNode"]
