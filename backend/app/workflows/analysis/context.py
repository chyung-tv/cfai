from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession


class WorkflowResult(TypedDict, total=False):
    id: str
    symbol: str
    reportMarkdown: str
    citations: list[dict[str, Any]]
    interactionId: str
    generatedAt: str
    modelMetadata: dict[str, Any]
    structuredOutput: dict[str, Any]
    reverseDcf: dict[str, Any]
    auditGrowthLikelihood: dict[str, Any]
    advisorDecision: dict[str, Any]


class WorkflowContext(TypedDict):
    workflow_id: str
    symbol: str
    force_refresh: bool
    db: AsyncSession
    result: NotRequired[WorkflowResult]
    cached_result: NotRequired[dict[str, Any]]
    catalog_id: NotRequired[int]
    catalog_name_display: NotRequired[str]
    catalog_name_normalized: NotRequired[str]
    deep_research_interaction_id: NotRequired[str]
    report_markdown: NotRequired[str]
    report_citations: NotRequired[list[dict[str, Any]]]
    report_generated_at: NotRequired[str]
    model_metadata: NotRequired[dict[str, Any]]
    structured_output: NotRequired[dict[str, Any]]
    reverse_dcf: NotRequired[dict[str, Any]]
    audit_growth_likelihood: NotRequired[dict[str, Any]]
    advisor_decision: NotRequired[dict[str, Any]]


__all__ = ["WorkflowContext", "WorkflowResult"]
