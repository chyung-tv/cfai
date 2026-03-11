from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
import copy
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.workflow.analysis_candidate_card import AnalysisCandidateCard
from app.models.workflow.stock_catalog import StockCatalog
from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_workflow_event import AnalysisWorkflowEvent
from app.models.workflow.analysis_symbol_snapshot import AnalysisSymbolSnapshot
from app.workflows.analysis.orchestrator import WorkflowOrchestrator
from app.workflows.analysis.projections.store import (
    portfolio_impact_signal_score,
    quality_score_value,
    recent_change_signal_score,
    valuation_signal_score,
)
from app.workflows.analysis.sse import SseBroker

ANALYSIS_FRESHNESS_TTL = timedelta(days=7)


def _with_freshness(payload: dict[str, Any], updated_at: datetime | None) -> dict[str, Any]:
    enriched = copy.deepcopy(payload)
    summary = enriched.get("summary")
    if not isinstance(summary, dict):
        return enriched
    freshness = summary.get("analysisFreshness")
    if not isinstance(freshness, dict):
        freshness = {}
        summary["analysisFreshness"] = freshness

    if updated_at is None:
        freshness["isFresh"] = None
        return enriched
    threshold = datetime.now(UTC) - ANALYSIS_FRESHNESS_TTL
    freshness["isFresh"] = updated_at >= threshold
    return enriched


def _is_fresh_from_timestamps(
    *,
    freshness_updated_at: datetime | None,
    freshness_expires_at: datetime | None,
) -> bool | None:
    now = datetime.now(UTC)
    if freshness_expires_at is not None:
        return freshness_expires_at >= now
    if freshness_updated_at is not None:
        return freshness_updated_at >= (now - ANALYSIS_FRESHNESS_TTL)
    return None


def _expected_return_range(
    quality: float,
    valuation: float,
    portfolio_impact: float,
) -> dict[str, float]:
    # Heuristic v1 range, bounded for stable UX output.
    midpoint = 2.0 + (quality * 12.0) + (valuation * 8.0) - ((1.0 - portfolio_impact) * 4.0)
    low = max(-8.0, midpoint - 5.0)
    high = min(35.0, midpoint + 5.0)
    return {"lowPct": round(low, 1), "highPct": round(high, 1)}


class TriggerBody(BaseModel):
    symbol: str


def create_workflow_router(
    orchestrator: WorkflowOrchestrator,
    sse_broker: SseBroker,
) -> APIRouter:
    router = APIRouter(prefix="/analysis", tags=["analysis"])

    @router.post("/trigger")
    async def trigger_analysis(
        body: TriggerBody,
        force: bool = Query(default=False),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, str]:
        symbol = body.symbol.strip().upper()
        if not symbol:
            raise HTTPException(status_code=400, detail="symbol is required")
        workflow_id = await orchestrator.start_workflow(
            db=db,
            symbol=symbol,
            force_refresh=force,
            user_id=None,
        )
        return {"status": "processing", "traceId": workflow_id}

    @router.get("/events")
    async def get_analysis_events(
        traceId: str | None = Query(default=None),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        query = select(AnalysisWorkflowEvent).order_by(desc(AnalysisWorkflowEvent.created_at))
        if traceId:
            query = query.where(AnalysisWorkflowEvent.workflow_id == traceId)
        result = await db.execute(query.limit(100))
        events = result.scalars().all()
        return {
            "events": [
                {
                    "id": event.id,
                    "seqNo": event.seq_no,
                    "state": event.state,
                    "substate": event.substate,
                    "eventType": event.event_type,
                    "message": event.message,
                    "payload": event.payload,
                    "createdAt": event.created_at.isoformat(),
                }
                for event in events
            ]
        }

    @router.get("/events/stream")
    async def stream_analysis_events(
        traceId: str | None = Query(default=None),
    ) -> StreamingResponse:
        async def _stream() -> AsyncGenerator[str, None]:
            async for item in sse_broker.subscribe(traceId):
                yield item

        return StreamingResponse(_stream(), media_type="text/event-stream")

    @router.get("/latest")
    async def get_latest_analysis(
        symbol: str,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any] | None:
        symbol = symbol.strip().upper()
        result = await db.execute(
            select(AnalysisSymbolSnapshot)
            .where(
                AnalysisSymbolSnapshot.symbol == symbol,
                AnalysisSymbolSnapshot.state.in_(["completed", "completed_cached"]),
            )
            .order_by(desc(AnalysisSymbolSnapshot.updated_at))
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if snapshot is not None:
            if isinstance(snapshot.summary, dict) and isinstance(snapshot.details, dict):
                payload = {
                    "summary": snapshot.summary,
                    "details": snapshot.details,
                    "modelMetadata": snapshot.model_metadata if isinstance(snapshot.model_metadata, dict) else {},
                }
                return _with_freshness(payload, snapshot.updated_at)
            return None

        # Backward-compatible fallback for older rows during transition.
        fallback = await db.execute(
            select(AnalysisWorkflow)
            .where(
                AnalysisWorkflow.symbol == symbol,
                AnalysisWorkflow.state.in_(["completed", "completed_cached"]),
            )
            .order_by(desc(AnalysisWorkflow.updated_at))
            .limit(1)
        )
        workflow = fallback.scalar_one_or_none()
        if workflow is None:
            return None
        # No legacy payload available after schema redesign.
        return None

    @router.get("/candidates")
    async def get_candidate_cards(
        sort_by: Literal["blended", "quality", "portfolio_impact", "valuation_recent"] = Query(
            default="blended"
        ),
        quality_weight: float = Query(default=0.4, ge=0.0, le=1.0),
        portfolio_impact_weight: float = Query(default=0.3, ge=0.0, le=1.0),
        valuation_recent_weight: float = Query(default=0.3, ge=0.0, le=1.0),
        limit: int = Query(default=100, ge=1, le=500),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        result = await db.execute(
            select(AnalysisCandidateCard, StockCatalog.name_display, StockCatalog.sector)
            .outerjoin(StockCatalog, StockCatalog.id == AnalysisCandidateCard.catalog_id)
            .order_by(desc(AnalysisCandidateCard.updated_at))
            .limit(500)
        )
        rows = result.all()
        total_weight = quality_weight + portfolio_impact_weight + valuation_recent_weight
        if total_weight <= 0:
            quality_weight = 0.4
            portfolio_impact_weight = 0.3
            valuation_recent_weight = 0.3
            total_weight = 1.0

        def _build_card(row: Any) -> dict[str, Any]:
            card, name_display, sector = row
            quality_component = quality_score_value(card.quality_score)
            valuation_component = valuation_signal_score(card.valuation_signal)
            recent_change_component = recent_change_signal_score(card.recent_change_signal)
            portfolio_impact_component = portfolio_impact_signal_score(card.portfolio_impact_signal)
            valuation_recent_component = round(
                (valuation_component + recent_change_component) / 2.0,
                4,
            )
            blended_score = round(
                (
                    (quality_component * quality_weight)
                    + (portfolio_impact_component * portfolio_impact_weight)
                    + (valuation_recent_component * valuation_recent_weight)
                )
                / total_weight,
                4,
            )
            expected_return = _expected_return_range(
                quality=quality_component,
                valuation=valuation_component,
                portfolio_impact=portfolio_impact_component,
            )
            return {
                "symbol": card.symbol,
                "name": name_display,
                "sector": sector,
                "qualityScore": card.quality_score,
                "valuationSignal": card.valuation_signal,
                "recentChangeSignal": card.recent_change_signal,
                "portfolioImpactSignal": card.portfolio_impact_signal,
                "freshnessUpdatedAt": card.freshness_updated_at.isoformat()
                if card.freshness_updated_at
                else None,
                "freshnessExpiresAt": card.freshness_expires_at.isoformat()
                if card.freshness_expires_at
                else None,
                "isFresh": _is_fresh_from_timestamps(
                    freshness_updated_at=card.freshness_updated_at,
                    freshness_expires_at=card.freshness_expires_at,
                ),
                "scores": {
                    "quality": quality_component,
                    "valuation": valuation_component,
                    "recentChange": recent_change_component,
                    "valuationRecent": valuation_recent_component,
                    "portfolioImpact": portfolio_impact_component,
                    "blended": blended_score,
                    "portfolioRisk": round(1.0 - portfolio_impact_component, 4),
                },
                "expectedReturnRange": expected_return,
                "payload": card.card_payload,
            }

        cards = [_build_card(row) for row in rows]

        def _sort_score(card: dict[str, Any]) -> float:
            scores = card.get("scores")
            if not isinstance(scores, dict):
                return 0.0
            if sort_by == "quality":
                return float(scores.get("quality") or 0.0)
            if sort_by == "portfolio_impact":
                return float(scores.get("portfolioImpact") or 0.0)
            if sort_by == "valuation_recent":
                return float(scores.get("valuationRecent") or 0.0)
            return float(scores.get("blended") or 0.0)

        cards.sort(key=lambda item: (-_sort_score(item), item["symbol"]))
        limited_cards = cards[:limit]
        return {
            "sortBy": sort_by,
            "weights": {
                "quality": quality_weight,
                "portfolioImpact": portfolio_impact_weight,
                "valuationRecent": valuation_recent_weight,
            },
            "cards": limited_cards,
        }

    @router.get("/workflows/{trace_id}/status")
    async def get_workflow_status(
        trace_id: str,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        workflow_result = await db.execute(
            select(AnalysisWorkflow).where(AnalysisWorkflow.id == trace_id)
        )
        workflow = workflow_result.scalar_one_or_none()
        if workflow is None:
            raise HTTPException(status_code=404, detail="workflow not found")
        last_event_result = await db.execute(
            select(AnalysisWorkflowEvent)
            .where(AnalysisWorkflowEvent.workflow_id == trace_id)
            .order_by(desc(AnalysisWorkflowEvent.created_at))
            .limit(1)
        )
        last_event = last_event_result.scalar_one_or_none()
        now = datetime.now(UTC)
        started_at = workflow.started_at or workflow.created_at
        elapsed_seconds = int((now - started_at).total_seconds()) if started_at else 0
        last_event_at = last_event.created_at if last_event is not None else None
        stale_threshold = max(10, settings.workflow_stale_progress_threshold_seconds)
        elapsed_without_progress = (
            int((now - last_event_at).total_seconds()) if last_event_at is not None else elapsed_seconds
        )
        is_stale = workflow.state == "running" and elapsed_without_progress >= stale_threshold
        return {
            "id": workflow.id,
            "symbol": workflow.symbol,
            "state": workflow.state,
            "substate": workflow.substate,
            "createdAt": workflow.created_at.isoformat(),
            "startedAt": started_at.isoformat() if started_at else None,
            "lastEventAt": last_event_at.isoformat() if last_event_at else None,
            "lastEventType": last_event.event_type if last_event else None,
            "elapsedSec": elapsed_seconds,
            "elapsedWithoutProgressSec": elapsed_without_progress,
            "staleThresholdSec": stale_threshold,
            "isStale": is_stale,
            "errorCode": workflow.error_code,
            "errorMessage": workflow.error_message,
        }

    @router.get("/workflows/{trace_id}/timeline")
    async def get_workflow_timeline(
        trace_id: str,
        limit: int = Query(default=500, ge=1, le=5000),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        workflow_result = await db.execute(
            select(AnalysisWorkflow).where(AnalysisWorkflow.id == trace_id)
        )
        workflow = workflow_result.scalar_one_or_none()
        if workflow is None:
            raise HTTPException(status_code=404, detail="workflow not found")
        events_result = await db.execute(
            select(AnalysisWorkflowEvent)
            .where(AnalysisWorkflowEvent.workflow_id == trace_id)
            .order_by(AnalysisWorkflowEvent.seq_no.asc())
            .limit(limit)
        )
        events = events_result.scalars().all()
        return {
            "id": workflow.id,
            "symbol": workflow.symbol,
            "state": workflow.state,
            "events": [
                {
                    "id": event.id,
                    "seqNo": event.seq_no,
                    "state": event.state,
                    "substate": event.substate,
                    "eventType": event.event_type,
                    "message": event.message,
                    "payload": event.payload,
                    "durationMs": event.payload.get("durationMs")
                    if isinstance(event.payload, dict)
                    else None,
                    "createdAt": event.created_at.isoformat(),
                }
                for event in events
            ],
        }

    @router.get("/history")
    async def get_analysis_history(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
        result = await db.execute(
            select(AnalysisWorkflow).order_by(desc(AnalysisWorkflow.created_at)).limit(100)
        )
        workflows = result.scalars().all()
        return [
            {
                "id": item.id,
                "symbol": item.symbol,
                "status": item.state,
                "traceId": item.id,
                "createdAt": item.created_at.isoformat(),
                "analysisResult": None,
            }
            for item in workflows
        ]

    @router.get("/query/{query_id}/sync")
    async def sync_query(
        query_id: str,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        result = await db.execute(select(AnalysisWorkflow).where(AnalysisWorkflow.id == query_id))
        workflow = result.scalar_one_or_none()
        if workflow is None:
            raise HTTPException(status_code=404, detail="query not found")
        return {"status": workflow.state, "analysisResultId": None}

    @router.post("/query/{query_id}/mark-failed")
    async def mark_query_failed(
        query_id: str,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, str]:
        ok = await orchestrator.mark_workflow_failed(db=db, workflow_id=query_id)
        if not ok:
            raise HTTPException(status_code=404, detail="query not found")
        return {"status": "failed"}

    return router
