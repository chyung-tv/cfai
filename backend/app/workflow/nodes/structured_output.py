from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError, create_model

from app.providers.gemini_deep_research import (
    DeepResearchProviderError,
    GeminiDeepResearchClient,
)
from app.workflow.base_node import BaseNode
from app.workflow.prompts.dynamic_structured_output_prompt import (
    build_dynamic_data_prompt,
    build_dynamic_schema_prompt,
)


class DynamicFieldSpec(BaseModel):
    name: str
    type: str
    required: bool = False
    description: str | None = None


class DynamicSchemaSpec(BaseModel):
    fields: list[DynamicFieldSpec]
    notes: str | None = None


class BaseStructuredOutput(BaseModel):
    ticker: str | None = None
    final_verdict: str | None = None
    life_line_thrive_factor: str | None = None


class DynamicQuality(BaseModel):
    parser_version: str
    extraction_confidence: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class DynamicStructuredEnvelope(BaseModel):
    base: BaseStructuredOutput
    dynamic_data: dict[str, Any]
    quality: DynamicQuality


class StructuredOutputNode(BaseNode):
    name = "structured_output"
    timeout_seconds = 60.0 * 5

    def __init__(self, client: GeminiDeepResearchClient) -> None:
        self._client = client

    async def run(self, context: dict) -> dict:
        result = context.get("result")
        if not isinstance(result, dict):
            raise ValueError("deep research result is missing")

        report_markdown = result.get("reportMarkdown")
        if not isinstance(report_markdown, str) or not report_markdown.strip():
            raise ValueError("reportMarkdown is required for structured output")

        try:
            schema_raw = await self._client.generate_json_object(
                prompt=build_dynamic_schema_prompt(report_markdown=report_markdown)
            )
        except DeepResearchProviderError as exc:
            raise RuntimeError(f"dynamic_schema_{exc.code}: {exc}") from exc

        try:
            schema_spec = DynamicSchemaSpec.model_validate(schema_raw)
        except ValidationError as exc:
            raise RuntimeError(f"dynamic_schema_validation_failed: {exc}") from exc

        if len(schema_spec.fields) == 0:
            raise RuntimeError("dynamic_schema_validation_failed: fields cannot be empty")

        try:
            data_raw = await self._client.generate_json_object(
                prompt=build_dynamic_data_prompt(
                    report_markdown=report_markdown,
                    schema_fields=[f.model_dump(mode="json") for f in schema_spec.fields],
                )
            )
        except DeepResearchProviderError as exc:
            raise RuntimeError(f"dynamic_data_{exc.code}: {exc}") from exc

        try:
            envelope = DynamicStructuredEnvelope.model_validate(data_raw)
        except ValidationError as exc:
            raise RuntimeError(f"dynamic_data_validation_failed: {exc}") from exc

        runtime_model = self._build_runtime_model(schema_spec.fields)
        try:
            validated_dynamic = runtime_model.model_validate(envelope.dynamic_data)
        except ValidationError as exc:
            raise RuntimeError(f"dynamic_fields_validation_failed: {exc}") from exc

        structured_output = {
            "base": envelope.base.model_dump(mode="json"),
            "dynamicSchema": schema_spec.model_dump(mode="json"),
            "dynamicData": validated_dynamic.model_dump(mode="json"),
            "quality": envelope.quality.model_dump(mode="json"),
        }
        result["structuredOutput"] = structured_output

        model_metadata = result.get("modelMetadata")
        if isinstance(model_metadata, dict):
            model_metadata["structuredOutput"] = {
                "mode": "dynamic_llm",
                "model": "gemini-2.5-flash",
                "fieldCount": len(schema_spec.fields),
            }
        else:
            result["modelMetadata"] = {
                "structuredOutput": {
                    "mode": "dynamic_llm",
                    "model": "gemini-2.5-flash",
                    "fieldCount": len(schema_spec.fields),
                }
            }

        context["structured_output"] = structured_output
        context["result"] = result
        return {"result": result, "structuredOutput": structured_output}

    @staticmethod
    def _build_runtime_model(fields: list[DynamicFieldSpec]) -> type[BaseModel]:
        model_fields: dict[str, tuple[type[Any], Any]] = {}
        for field in fields:
            py_type: type[Any]
            if field.type == "number":
                py_type = float
            elif field.type == "boolean":
                py_type = bool
            elif field.type == "array_string":
                py_type = list[str]
            else:
                py_type = str

            if field.required:
                model_fields[field.name] = (py_type, ...)
            else:
                model_fields[field.name] = (py_type | None, None)

        return create_model("DynamicStructuredDataModel", **model_fields)
