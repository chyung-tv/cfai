from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_workflow_projection import AnalysisWorkflowProjection
from app.workflows.analysis.projections.normalizer import (
    CONTRACT_VERSION,
    normalize_projection_payload,
)


async def upsert_workflow_projection(
    db: AsyncSession,
    workflow: AnalysisWorkflow,
    *,
    message: str | None = None,
    latest_event_at: datetime | None = None,
    artifact_type: str | None = None,
    artifact_payload: dict[str, Any] | None = None,
) -> None:
    projection = await db.get(AnalysisWorkflowProjection, workflow.id)
    if projection is None:
        projection = AnalysisWorkflowProjection(workflow_id=workflow.id)

    normalized_payload, warnings = normalize_projection_payload(
        base_payload=workflow.result_payload if isinstance(workflow.result_payload, dict) else None,
        artifact_type=artifact_type,
        artifact_payload=artifact_payload,
    )

    projection.symbol = workflow.symbol
    projection.state = workflow.state
    projection.substate = workflow.substate
    projection.message = message
    projection.latest_event_at = latest_event_at or datetime.now(timezone.utc)
    projection.contract_version = CONTRACT_VERSION
    projection.result_payload = normalized_payload
    projection.structured_output = (
        normalized_payload.get("structuredOutput")
        if isinstance(normalized_payload.get("structuredOutput"), dict)
        else None
    )
    projection.reverse_dcf = (
        normalized_payload.get("reverseDcf")
        if isinstance(normalized_payload.get("reverseDcf"), dict)
        else None
    )
    projection.audit_growth_likelihood = (
        normalized_payload.get("auditGrowthLikelihood")
        if isinstance(normalized_payload.get("auditGrowthLikelihood"), dict)
        else None
    )
    projection.advisor_decision = (
        normalized_payload.get("advisorDecision")
        if isinstance(normalized_payload.get("advisorDecision"), dict)
        else None
    )
    projection.normalization_warnings = {"items": warnings} if warnings else None
    db.add(projection)
