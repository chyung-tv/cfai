from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_candidate_card import AnalysisCandidateCard
from app.models.workflow.analysis_symbol_snapshot import AnalysisSymbolSnapshot
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
    normalized_payload, warnings = normalize_projection_payload(
        base_payload=context_payload(workflow),
        artifact_type=artifact_type,
        artifact_payload=artifact_payload,
    )
    current_event_at = latest_event_at or datetime.now(timezone.utc)

    snapshot = await db.get(AnalysisSymbolSnapshot, workflow.symbol)
    if snapshot is None:
        snapshot = AnalysisSymbolSnapshot(symbol=workflow.symbol)
    snapshot.catalog_id = workflow.catalog_id
    snapshot.latest_workflow_id = workflow.id
    snapshot.state = workflow.state
    snapshot.summary = normalized_payload.get("summary") if isinstance(normalized_payload.get("summary"), dict) else None
    snapshot.details = normalized_payload.get("details") if isinstance(normalized_payload.get("details"), dict) else None
    snapshot.model_metadata = normalized_payload.get("modelMetadata") if isinstance(normalized_payload.get("modelMetadata"), dict) else None
    snapshot.freshness_expires_at = current_event_at.replace(microsecond=0) if workflow.state in {"completed", "completed_cached"} else None
    snapshot.contract_version = CONTRACT_VERSION
    snapshot.updated_at = current_event_at
    db.add(snapshot)

    card = await db.get(AnalysisCandidateCard, workflow.symbol)
    if card is None:
        card = AnalysisCandidateCard(symbol=workflow.symbol)
    summary = snapshot.summary if isinstance(snapshot.summary, dict) else {}
    card.catalog_id = workflow.catalog_id
    card.latest_workflow_id = workflow.id
    card.quality_score = _quality_score(summary)
    card.valuation_signal = _valuation_signal(summary)
    card.recent_change_signal = _recent_change_signal(normalized_payload)
    card.portfolio_impact_signal = _portfolio_impact_signal(normalized_payload)
    card.freshness_updated_at = current_event_at
    card.freshness_expires_at = snapshot.freshness_expires_at
    card.card_payload = {
        "symbol": workflow.symbol,
        "state": workflow.state,
        "message": message,
        "summary": summary,
        "warnings": warnings,
    }
    card.updated_at = current_event_at
    db.add(card)


def context_payload(workflow: AnalysisWorkflow) -> dict[str, Any] | None:
    # Result payload is now sourced from artifacts; workflow row is metadata only.
    raw = getattr(workflow, "result_payload", None)
    return raw if isinstance(raw, dict) else None


def _quality_score(summary: dict[str, Any]) -> float | None:
    business = summary.get("businessQuality") if isinstance(summary.get("businessQuality"), dict) else None
    tier = (business.get("tier") or "").strip().lower() if isinstance(business, dict) else ""
    mapping = {
        "elite": 1.0,
        "high": 0.85,
        "medium": 0.6,
        "low": 0.3,
    }
    return mapping.get(tier)


def _valuation_signal(summary: dict[str, Any]) -> str | None:
    valuation = (
        summary.get("valuationLegitimacy")
        if isinstance(summary.get("valuationLegitimacy"), dict)
        else None
    )
    label = valuation.get("label") if isinstance(valuation, dict) else None
    if isinstance(label, str) and label.strip():
        return label.strip().lower()
    return None


def _recent_change_signal(payload: dict[str, Any]) -> str | None:
    details = payload.get("details") if isinstance(payload.get("details"), dict) else None
    advisor = details.get("advisorDecision") if isinstance(details, dict) and isinstance(details.get("advisorDecision"), dict) else None
    actions = advisor.get("actions") if isinstance(advisor, dict) else None
    if isinstance(actions, list) and actions:
        return "has_new_action"
    return "stable"


def _portfolio_impact_signal(payload: dict[str, Any]) -> str | None:
    details = payload.get("details") if isinstance(payload.get("details"), dict) else None
    reverse_dcf = details.get("reverseDcf") if isinstance(details, dict) and isinstance(details.get("reverseDcf"), dict) else None
    summary = reverse_dcf.get("summary") if isinstance(reverse_dcf, dict) and isinstance(reverse_dcf.get("summary"), dict) else None
    median = summary.get("medianRevenueCagrPct") if isinstance(summary, dict) else None
    try:
        value = float(median)
    except (TypeError, ValueError):
        return "unknown"
    if value >= 20:
        return "high_risk_growth_assumption"
    if value >= 12:
        return "moderate_risk_growth_assumption"
    return "supportive_growth_assumption"
