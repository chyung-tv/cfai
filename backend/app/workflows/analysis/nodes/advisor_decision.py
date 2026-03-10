from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.core.workflow.base_node import BaseNode
from app.providers.advisor_client import AdvisorClient
from app.workflows.analysis.context import WorkflowContext
from app.workflows.analysis.prompts.advisor_decision_prompt import (
    build_advisor_decision_prompt,
)


class AdvisorQuality(BaseModel):
    parserVersion: str
    missingFields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("parserVersion")
    @classmethod
    def _validate_parser_version(cls, value: str) -> str:
        if value != "v1-advisor-decision":
            raise ValueError("parserVersion must be v1-advisor-decision")
        return value


class AdvisorProfileDecision(BaseModel):
    caseName: Literal["optimistic", "median", "conservative"]
    requiredRevenueCagrPct: float
    action: Literal["accumulate", "hold", "trim", "avoid"]
    advice: str = Field(min_length=1, max_length=320)
    reasoning: str = Field(min_length=1)
    evidenceRefs: list[str] = Field(min_length=1)
    keyRisks: list[str] = Field(min_length=2)
    invalidateConditions: list[str] = Field(min_length=2)

    @field_validator("evidenceRefs")
    @classmethod
    def _validate_refs(cls, value: list[str]) -> list[str]:
        for item in value:
            if not isinstance(item, str) or not item.startswith("sec:"):
                raise ValueError("evidenceRefs entries must start with sec:")
        return value


class AdvisorProfileEnvelope(BaseModel):
    profile: Literal["cash_preservation", "balanced_compounder", "capital_multiplier"]
    profileSummary: str = Field(min_length=1)
    caseAdvisories: list[AdvisorProfileDecision] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def _validate_case_advisories(self) -> "AdvisorProfileEnvelope":
        expected = {"optimistic", "median", "conservative"}
        observed = {item.caseName for item in self.caseAdvisories}
        if observed != expected:
            raise ValueError("caseAdvisories must include optimistic, median, conservative exactly once")
        return self


class AdvisorDecisionEnvelope(BaseModel):
    symbol: str
    projectionYears: int
    overallCall: str
    profiles: list[AdvisorProfileEnvelope] = Field(min_length=3, max_length=3)
    quality: AdvisorQuality

    @model_validator(mode="after")
    def _validate_profiles(self) -> "AdvisorDecisionEnvelope":
        expected = {"cash_preservation", "balanced_compounder", "capital_multiplier"}
        observed = {p.profile for p in self.profiles}
        if observed != expected:
            raise ValueError("profiles must include cash_preservation, balanced_compounder, capital_multiplier exactly once")
        return self


class AdvisorDecisionNode(BaseNode):
    name = "advisor_decision"
    timeout_seconds = 60.0 * 3

    def __init__(self, client: AdvisorClient) -> None:
        self._client = client

    async def run(self, context: WorkflowContext) -> dict:
        result = context.get("result")
        if not isinstance(result, dict):
            raise ValueError("result payload is required")

        symbol = str(result.get("symbol") or context.get("symbol") or "").strip().upper()
        if not symbol:
            raise ValueError("symbol is required for advisor decision")

        report_markdown = result.get("reportMarkdown")
        if not isinstance(report_markdown, str) or not report_markdown.strip():
            raise ValueError("reportMarkdown is required for advisor decision")

        reverse_dcf = result.get("reverseDcf")
        if not isinstance(reverse_dcf, dict):
            raise ValueError("reverseDcf is required for advisor decision")
        summary = reverse_dcf.get("summary")
        if not isinstance(summary, dict):
            raise ValueError("reverseDcf.summary is required for advisor decision")

        audit_growth = result.get("auditGrowthLikelihood")
        if not isinstance(audit_growth, dict):
            raise ValueError("auditGrowthLikelihood is required for advisor decision")
        audit_cases = audit_growth.get("cases")
        if not isinstance(audit_cases, list) or len(audit_cases) == 0:
            raise ValueError("auditGrowthLikelihood.cases is required for advisor decision")

        optimistic = self._as_float(summary.get("bestCaseRevenueCagrPct"))
        median = self._as_float(summary.get("medianRevenueCagrPct"))
        conservative = self._as_float(summary.get("worstCaseRevenueCagrPct"))
        if optimistic is None or median is None or conservative is None:
            raise ValueError("reverseDcf summary CAGR values are required for advisor decision")

        projection_years = int(reverse_dcf.get("projectionYears") or 10)

        prompt = build_advisor_decision_prompt(
            symbol=symbol,
            projection_years=projection_years,
            optimistic_cagr_pct=optimistic,
            median_cagr_pct=median,
            conservative_cagr_pct=conservative,
            audit_cases=audit_cases,
            report_markdown=report_markdown,
        )
        try:
            raw = await self._client.generate_advisor_decision(prompt=prompt)
        except Exception as exc:
            raise RuntimeError(f"advisor_decision_provider_error: {exc}") from exc

        try:
            envelope = AdvisorDecisionEnvelope.model_validate(raw)
        except ValidationError as exc:
            raise RuntimeError(f"advisor_decision_validation_failed: {exc}") from exc

        if envelope.symbol.strip().upper() != symbol:
            raise RuntimeError("advisor_decision_symbol_mismatch")
        if envelope.projectionYears != projection_years:
            raise RuntimeError("advisor_decision_projection_years_mismatch")
        expected_case_cagr = {
            "optimistic": optimistic,
            "median": median,
            "conservative": conservative,
        }
        self._validate_case_cagrs(envelope=envelope, expected=expected_case_cagr)

        advisor_payload = envelope.model_dump(mode="json")
        result["advisorDecision"] = advisor_payload

        model_metadata = result.get("modelMetadata")
        if isinstance(model_metadata, dict):
            model_metadata["advisorDecision"] = {
                "model": self._client.model_name,
                "mode": "structured_json",
                "projectionYears": projection_years,
            }
        else:
            result["modelMetadata"] = {
                "advisorDecision": {
                    "model": self._client.model_name,
                    "mode": "structured_json",
                    "projectionYears": projection_years,
                }
            }

        context["advisor_decision"] = advisor_payload
        context["result"] = result
        return {"result": result, "advisorDecision": advisor_payload}

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

    @staticmethod
    def _validate_case_cagrs(
        *,
        envelope: AdvisorDecisionEnvelope,
        expected: dict[str, float],
    ) -> None:
        for profile in envelope.profiles:
            observed = {item.caseName: item.requiredRevenueCagrPct for item in profile.caseAdvisories}
            for case_name, expected_value in expected.items():
                value = observed.get(case_name)
                if value is None:
                    raise RuntimeError(f"advisor_decision_missing_case: {profile.profile}.{case_name}")
                if abs(value - expected_value) > 1e-6:
                    raise RuntimeError(
                        f"advisor_decision_case_cagr_mismatch: {profile.profile}.{case_name} expected {expected_value} got {value}"
                    )


__all__ = ["AdvisorDecisionNode"]
