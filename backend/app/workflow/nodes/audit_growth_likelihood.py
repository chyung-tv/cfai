from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.providers.gemini_deep_research import (
    DeepResearchProviderError,
    GeminiDeepResearchClient,
)
from app.workflow.base_node import BaseNode
from app.workflow.context import WorkflowContext
from app.workflow.prompts.audit_growth_likelihood_prompt import (
    build_audit_growth_likelihood_prompt,
)


class AuditQuality(BaseModel):
    parserVersion: str
    missingFields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("parserVersion")
    @classmethod
    def _validate_parser_version(cls, value: str) -> str:
        if value != "v1-audit-growth-likelihood":
            raise ValueError("parserVersion must be v1-audit-growth-likelihood")
        return value


class AuditCase(BaseModel):
    caseName: Literal["optimistic", "median", "conservative"]
    requiredRevenueCagrPct: float
    probabilityPct: float
    likelihoodLabel: Literal["likely", "possible", "unlikely"]
    rationale: str = Field(min_length=80)
    claimRefs: list[str] = Field(min_length=1)
    risksToThesis: list[str] = Field(min_length=2)
    supportingDrivers: list[str] = Field(min_length=2)

    @field_validator("probabilityPct")
    @classmethod
    def _validate_probability(cls, value: float) -> float:
        if value < 0.0 or value > 100.0:
            raise ValueError("probabilityPct must be between 0 and 100")
        return value

    @field_validator("claimRefs")
    @classmethod
    def _validate_claim_refs(cls, value: list[str]) -> list[str]:
        if len(value) == 0:
            raise ValueError("claimRefs must contain at least one reference")
        for ref in value:
            if not isinstance(ref, str) or not ref.startswith("sec:"):
                raise ValueError("claimRefs entries must start with sec:")
        return value


class AuditGrowthLikelihoodEnvelope(BaseModel):
    projectionYears: int
    overallAssessment: str
    cases: list[AuditCase] = Field(min_length=3, max_length=3)
    quality: AuditQuality

    @model_validator(mode="after")
    def _validate_cases(self) -> "AuditGrowthLikelihoodEnvelope":
        case_names = {case.caseName for case in self.cases}
        expected = {"optimistic", "median", "conservative"}
        if case_names != expected:
            raise ValueError("cases must include optimistic, median, conservative exactly once")
        return self


class AuditGrowthLikelihoodNode(BaseNode):
    name = "audit_growth_likelihood"
    timeout_seconds = 60.0 * 3

    def __init__(self, client: GeminiDeepResearchClient) -> None:
        self._client = client

    async def run(self, context: WorkflowContext) -> dict:
        result = context.get("result")
        if not isinstance(result, dict):
            raise ValueError("result payload is required")

        report_markdown = result.get("reportMarkdown")
        if not isinstance(report_markdown, str) or not report_markdown.strip():
            raise ValueError("reportMarkdown is required for audit growth likelihood")

        reverse_dcf = result.get("reverseDcf")
        if not isinstance(reverse_dcf, dict):
            raise ValueError("reverseDcf is required for audit growth likelihood")

        summary = reverse_dcf.get("summary")
        if not isinstance(summary, dict):
            raise ValueError("reverseDcf.summary is required for audit growth likelihood")

        optimistic = self._as_float(summary.get("bestCaseRevenueCagrPct"))
        median = self._as_float(summary.get("medianRevenueCagrPct"))
        conservative = self._as_float(summary.get("worstCaseRevenueCagrPct"))
        if optimistic is None or median is None or conservative is None:
            raise ValueError("reverseDcf.summary CAGR values are required for audit growth likelihood")

        projection_years = int(reverse_dcf.get("projectionYears") or 10)
        symbol = str(result.get("symbol") or context.get("symbol") or "").strip().upper()
        if not symbol:
            raise ValueError("symbol is required for audit growth likelihood")

        prompt = build_audit_growth_likelihood_prompt(
            symbol=symbol,
            projection_years=projection_years,
            optimistic_cagr_pct=optimistic,
            median_cagr_pct=median,
            conservative_cagr_pct=conservative,
            report_markdown=report_markdown,
        )
        try:
            raw = await self._client.generate_json_object(prompt=prompt)
        except DeepResearchProviderError as exc:
            raise RuntimeError(f"audit_growth_likelihood_{exc.code}: {exc}") from exc

        try:
            envelope = AuditGrowthLikelihoodEnvelope.model_validate(raw)
        except ValidationError as exc:
            raise RuntimeError(f"audit_growth_likelihood_validation_failed: {exc}") from exc

        self._validate_case_cagrs(
            envelope=envelope,
            expected={
                "optimistic": optimistic,
                "median": median,
                "conservative": conservative,
            },
        )

        audit_payload = envelope.model_dump(mode="json")
        result["auditGrowthLikelihood"] = audit_payload

        model_metadata = result.get("modelMetadata")
        if isinstance(model_metadata, dict):
            model_metadata["auditGrowthLikelihood"] = {
                "model": "gemini-2.5-flash",
                "mode": "structured_json",
                "projectionYears": projection_years,
            }
        else:
            result["modelMetadata"] = {
                "auditGrowthLikelihood": {
                    "model": "gemini-2.5-flash",
                    "mode": "structured_json",
                    "projectionYears": projection_years,
                }
            }

        context["audit_growth_likelihood"] = audit_payload
        context["result"] = result
        return {"result": result, "auditGrowthLikelihood": audit_payload}

    @staticmethod
    def _validate_case_cagrs(
        *,
        envelope: AuditGrowthLikelihoodEnvelope,
        expected: dict[str, float],
    ) -> None:
        observed = {case.caseName: case.requiredRevenueCagrPct for case in envelope.cases}
        for case_name, expected_value in expected.items():
            value = observed.get(case_name)
            if value is None:
                raise RuntimeError(f"audit_growth_likelihood_missing_case: {case_name}")
            if abs(value - expected_value) > 1e-6:
                raise RuntimeError(
                    f"audit_growth_likelihood_case_cagr_mismatch: {case_name} expected {expected_value} got {value}"
                )

    @staticmethod
    def _as_float(value: object) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            raw = value.strip().replace(",", "")
            if not raw:
                return None
            try:
                return float(raw)
            except ValueError:
                return None
        return None
