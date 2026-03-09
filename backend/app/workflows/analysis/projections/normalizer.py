from __future__ import annotations

import copy
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = 1
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

    normalized = ProjectionContract(
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
    return normalized.model_dump(), warnings
