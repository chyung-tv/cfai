from __future__ import annotations

import copy
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = 2
KNOWN_ARTIFACT_TYPES = {
    "structured_output": "structuredOutput",
    "reverse_dcf": "reverseDcf",
    "audit_growth_likelihood": "auditGrowthLikelihood",
    "advisor_decision": "advisorDecision",
    "final_result": None,
    "deep_research": None,
    "deep_research_fixture": None,
}


class ProjectionContract(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: dict[str, Any]
    details: dict[str, Any]
    modelMetadata: dict[str, Any] | None = None


class InvestmentThesisSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str | None = None


class BusinessQualitySubfactors(BaseModel):
    model_config = ConfigDict(extra="ignore")

    moatStrength: str | None = None
    managementExecution: str | None = None
    industryPositioning: str | None = None


class BusinessQualitySummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tier: str | None = None
    subfactors: BusinessQualitySubfactors


class ValuationLegitimacySummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str | None = None
    basis: str | None = None


class AnalysisFreshnessSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    isFresh: bool | None = None


class SummaryContract(BaseModel):
    model_config = ConfigDict(extra="ignore")

    investmentThesis: InvestmentThesisSummary
    businessQuality: BusinessQualitySummary
    valuationLegitimacy: ValuationLegitimacySummary
    analysisFreshness: AnalysisFreshnessSummary


class DetailsContract(BaseModel):
    model_config = ConfigDict(extra="ignore")

    structuredOutput: dict[str, Any] | None = None
    reverseDcf: dict[str, Any] | None = None
    auditGrowthLikelihood: dict[str, Any] | None = None
    advisorDecision: dict[str, Any] | None = None
    reportMarkdown: str | None = None
    citations: list[Any] = Field(default_factory=list)


def _copy_dict(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return copy.deepcopy(value)


def _copy_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return copy.deepcopy(value)


def _pick_median_case(audit_growth_likelihood: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(audit_growth_likelihood, dict):
        return None
    cases = audit_growth_likelihood.get("cases")
    if not isinstance(cases, list):
        return None
    for item in cases:
        if isinstance(item, dict) and str(item.get("caseName")).strip().lower() == "median":
            return item
    return None


def _as_float(value: Any) -> float | None:
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


def _valuation_legitimacy(
    *,
    reverse_dcf: dict[str, Any] | None,
    audit_growth_likelihood: dict[str, Any] | None,
) -> ValuationLegitimacySummary:
    summary = reverse_dcf.get("summary") if isinstance(reverse_dcf, dict) else None
    median_required = _as_float(summary.get("medianRevenueCagrPct")) if isinstance(summary, dict) else None
    median_case = _pick_median_case(audit_growth_likelihood)
    median_likelihood = (
        str(median_case.get("likelihoodLabel")).strip().lower()
        if isinstance(median_case, dict) and median_case.get("likelihoodLabel") is not None
        else None
    )
    median_probability = (
        _as_float(median_case.get("probabilityPct")) if isinstance(median_case, dict) else None
    )

    if median_required is None or median_likelihood is None:
        return ValuationLegitimacySummary(label=None, basis=None)

    if median_likelihood == "unlikely" or median_required >= 25.0:
        label = "Unlikely"
    elif median_likelihood == "possible" or median_required >= 15.0:
        label = "Stretch"
    else:
        label = "Legitimate"

    basis_parts = [f"median required CAGR {round(median_required, 2)}%"]
    basis_parts.append(f"median likelihood {median_likelihood}")
    if median_probability is not None:
        basis_parts.append(f"median probability {round(median_probability, 2)}%")
    return ValuationLegitimacySummary(label=label, basis=", ".join(basis_parts))


def normalize_projection_payload(
    *,
    base_payload: dict[str, Any] | None,
    artifact_type: str | None = None,
    artifact_payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    candidate: dict[str, Any] = copy.deepcopy(base_payload) if isinstance(base_payload, dict) else {}

    if artifact_type is not None:
        if artifact_type not in KNOWN_ARTIFACT_TYPES:
            warnings.append(f"unknown_artifact_type:{artifact_type}")
        elif artifact_type == "final_result":
            if isinstance(artifact_payload, dict):
                candidate = copy.deepcopy(artifact_payload)
            else:
                warnings.append("final_result_artifact_not_dict")
        else:
            target_key = KNOWN_ARTIFACT_TYPES[artifact_type]
            if target_key is not None and isinstance(artifact_payload, dict):
                candidate[target_key] = copy.deepcopy(artifact_payload)

    details = DetailsContract(
        structuredOutput=_copy_dict(candidate.get("structuredOutput")),
        reverseDcf=_copy_dict(candidate.get("reverseDcf")),
        auditGrowthLikelihood=_copy_dict(candidate.get("auditGrowthLikelihood")),
        advisorDecision=_copy_dict(candidate.get("advisorDecision")),
        reportMarkdown=(
            candidate.get("reportMarkdown")
            if isinstance(candidate.get("reportMarkdown"), str)
            else None
        ),
        citations=_copy_list(candidate.get("citations")),
    )
    structured = details.structuredOutput if isinstance(details.structuredOutput, dict) else None
    business_quality = structured.get("businessQuality") if isinstance(structured, dict) else None
    management_profile = structured.get("managementProfile") if isinstance(structured, dict) else None
    industry_profile = structured.get("industryProfile") if isinstance(structured, dict) else None
    executive_summary = structured.get("executiveSummary") if isinstance(structured, dict) else None

    moat_strength = None
    if isinstance(business_quality, dict):
        moat = business_quality.get("moat")
        if isinstance(moat, list) and moat:
            first_moat = moat[0]
            moat_strength = first_moat if isinstance(first_moat, str) else None

    management_execution = None
    if isinstance(management_profile, dict):
        leader = management_profile.get("leadershipSummary")
        management_execution = leader if isinstance(leader, str) else None

    industry_positioning = None
    if isinstance(industry_profile, dict):
        position_rationale = industry_profile.get("positionRationale")
        position = industry_profile.get("position")
        if isinstance(position_rationale, str) and position_rationale.strip():
            industry_positioning = position_rationale
        elif isinstance(position, str):
            industry_positioning = position

    thesis_text = None
    if isinstance(executive_summary, dict):
        summary_text = executive_summary.get("summary")
        thesis_text = summary_text if isinstance(summary_text, str) else None

    valuation_legitimacy = _valuation_legitimacy(
        reverse_dcf=details.reverseDcf,
        audit_growth_likelihood=details.auditGrowthLikelihood,
    )

    normalized = ProjectionContract(
        summary=SummaryContract(
            investmentThesis=InvestmentThesisSummary(text=thesis_text),
            businessQuality=BusinessQualitySummary(
                tier=(
                    business_quality.get("qualityTier")
                    if isinstance(business_quality, dict)
                    and isinstance(business_quality.get("qualityTier"), str)
                    else None
                ),
                subfactors=BusinessQualitySubfactors(
                    moatStrength=moat_strength,
                    managementExecution=management_execution,
                    industryPositioning=industry_positioning,
                ),
            ),
            valuationLegitimacy=valuation_legitimacy,
            analysisFreshness=AnalysisFreshnessSummary(isFresh=None),
        ).model_dump(),
        details=details.model_dump(),
        modelMetadata=_copy_dict(candidate.get("modelMetadata")),
    )
    return normalized.model_dump(), warnings
