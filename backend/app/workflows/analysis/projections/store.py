from __future__ import annotations

import copy
from datetime import datetime, timezone
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_candidate_card import AnalysisCandidateCard
from app.models.workflow.analysis_symbol_snapshot import AnalysisSymbolSnapshot
from app.workflows.analysis.projections.normalizer import (
    CONTRACT_VERSION,
    normalize_projection_payload,
)

logger = logging.getLogger(__name__)

DEFAULT_QUALITY_SCORE = 0.5
DEFAULT_VALUATION_SCORE = 0.5
DEFAULT_RECENT_CHANGE_SCORE = 0.5
DEFAULT_PORTFOLIO_IMPACT_SCORE = 0.5

VALUATION_SIGNAL_SCORES: dict[str, float] = {
    "legitimate": 1.0,
    "stretch": 0.55,
    "unlikely": 0.2,
}

RECENT_CHANGE_SIGNAL_SCORES: dict[str, float] = {
    "has_new_action": 0.65,
    "stable": 0.5,
}

PORTFOLIO_IMPACT_SIGNAL_SCORES: dict[str, float] = {
    "supportive_growth_assumption": 0.95,
    "moderate_risk_growth_assumption": 0.55,
    "high_risk_growth_assumption": 0.2,
    "unknown": 0.5,
}


async def upsert_workflow_projection(
    db: AsyncSession,
    workflow: AnalysisWorkflow,
    *,
    message: str | None = None,
    latest_event_at: datetime | None = None,
    artifact_type: str | None = None,
    artifact_payload: dict[str, Any] | None = None,
) -> None:
    snapshot = await db.get(AnalysisSymbolSnapshot, workflow.symbol)
    normalized_payload, warnings = normalize_projection_payload(
        base_payload=merge_base_payload(
            workflow_payload=context_payload(workflow),
            snapshot=snapshot,
        ),
        artifact_type=artifact_type,
        artifact_payload=artifact_payload,
    )
    current_event_at = latest_event_at or datetime.now(timezone.utc)
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
    logger.info(
        "projection_updated trace_id=%s symbol=%s state=%s artifact_type=%s",
        workflow.id,
        workflow.symbol,
        workflow.state,
        artifact_type,
        extra={
            "trace_id": workflow.id,
            "symbol": workflow.symbol,
            "event_type": "projection_updated",
            "substate": workflow.substate,
        },
    )


def context_payload(workflow: AnalysisWorkflow) -> dict[str, Any] | None:
    # Result payload is now sourced from artifacts; workflow row is metadata only.
    raw = getattr(workflow, "result_payload", None)
    return raw if isinstance(raw, dict) else None


def merge_base_payload(
    *,
    workflow_payload: dict[str, Any] | None,
    snapshot: AnalysisSymbolSnapshot | None,
) -> dict[str, Any] | None:
    base = copy.deepcopy(workflow_payload) if isinstance(workflow_payload, dict) else {}
    if snapshot is None:
        return base or None
    details = snapshot.details if isinstance(snapshot.details, dict) else {}
    # Projection normalizer expects top-level artifact keys, so remap snapshot details back.
    for key in (
        "structuredOutput",
        "reverseDcf",
        "auditGrowthLikelihood",
        "advisorDecision",
        "reportMarkdown",
        "citations",
    ):
        if key not in base and key in details:
            base[key] = copy.deepcopy(details[key])
    if "modelMetadata" not in base and isinstance(snapshot.model_metadata, dict):
        base["modelMetadata"] = copy.deepcopy(snapshot.model_metadata)
    return base or None


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


def quality_score_value(value: float | None) -> float:
    if value is None:
        return DEFAULT_QUALITY_SCORE
    return max(0.0, min(1.0, float(value)))


def valuation_signal_score(signal: str | None) -> float:
    if not isinstance(signal, str):
        return DEFAULT_VALUATION_SCORE
    return VALUATION_SIGNAL_SCORES.get(signal.strip().lower(), DEFAULT_VALUATION_SCORE)


def recent_change_signal_score(signal: str | None) -> float:
    if not isinstance(signal, str):
        return DEFAULT_RECENT_CHANGE_SCORE
    return RECENT_CHANGE_SIGNAL_SCORES.get(signal.strip().lower(), DEFAULT_RECENT_CHANGE_SCORE)


def portfolio_impact_signal_score(signal: str | None) -> float:
    if not isinstance(signal, str):
        return DEFAULT_PORTFOLIO_IMPACT_SCORE
    return PORTFOLIO_IMPACT_SIGNAL_SCORES.get(
        signal.strip().lower(),
        DEFAULT_PORTFOLIO_IMPACT_SCORE,
    )
