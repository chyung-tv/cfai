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
from app.models.workflow.analysis_workflow_artifact import AnalysisWorkflowArtifact
from app.models.workflow.analysis_workflow_event import AnalysisWorkflowEvent
from app.models.workflow.analysis_symbol_snapshot import AnalysisSymbolSnapshot
from app.workflows.analysis.orchestrator import WorkflowOrchestrator
from app.workflows.analysis.services import (
    calculate_portfolio_metrics,
    default_portfolio_metrics,
    list_candidate_cards,
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


class TriggerBody(BaseModel):
    symbol: str


class PortfolioPositionBody(BaseModel):
    symbol: str
    weight: float


class PortfolioMetricsBody(BaseModel):
    positions: list[PortfolioPositionBody]


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
        return await list_candidate_cards(
            db,
            sort_by=sort_by,
            quality_weight=quality_weight,
            portfolio_impact_weight=portfolio_impact_weight,
            valuation_recent_weight=valuation_recent_weight,
            limit=limit,
        )

    @router.post("/portfolio/metrics")
    async def get_portfolio_metrics(
        body: PortfolioMetricsBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        clean_positions: list[tuple[str, float]] = []
        for position in body.positions:
            symbol = position.symbol.strip().upper()
            if not symbol:
                continue
            weight = max(0.0, min(100.0, float(position.weight)))
            clean_positions.append((symbol, weight))
        if not clean_positions:
            return default_portfolio_metrics()
        return await calculate_portfolio_metrics(db, positions=clean_positions)

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

    @router.get("/workflows/{trace_id}/persistence")
    async def get_workflow_persistence(
        trace_id: str,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        workflow_result = await db.execute(
            select(AnalysisWorkflow).where(AnalysisWorkflow.id == trace_id)
        )
        workflow = workflow_result.scalar_one_or_none()
        if workflow is None:
            raise HTTPException(status_code=404, detail="workflow not found")

        artifacts_result = await db.execute(
            select(AnalysisWorkflowArtifact)
            .where(AnalysisWorkflowArtifact.workflow_id == trace_id)
            .order_by(AnalysisWorkflowArtifact.produced_at.asc())
        )
        artifacts = artifacts_result.scalars().all()
        event_result = await db.execute(
            select(AnalysisWorkflowEvent)
            .where(AnalysisWorkflowEvent.workflow_id == trace_id)
            .order_by(desc(AnalysisWorkflowEvent.created_at))
            .limit(1)
        )
        latest_event = event_result.scalar_one_or_none()
        snapshot_result = await db.execute(
            select(AnalysisSymbolSnapshot).where(AnalysisSymbolSnapshot.symbol == workflow.symbol)
        )
        snapshot = snapshot_result.scalar_one_or_none()

        details = snapshot.details if snapshot is not None and isinstance(snapshot.details, dict) else None
        summary = snapshot.summary if snapshot is not None and isinstance(snapshot.summary, dict) else None
        model_metadata = (
            snapshot.model_metadata if snapshot is not None and isinstance(snapshot.model_metadata, dict) else None
        )
        return {
            "workflow": {
                "id": workflow.id,
                "symbol": workflow.symbol,
                "state": workflow.state,
                "substate": workflow.substate,
                "errorCode": workflow.error_code,
                "errorMessage": workflow.error_message,
                "createdAt": workflow.created_at.isoformat(),
                "updatedAt": workflow.updated_at.isoformat(),
                "completedAt": workflow.completed_at.isoformat() if workflow.completed_at else None,
            },
            "latestEvent": (
                {
                    "state": latest_event.state,
                    "substate": latest_event.substate,
                    "eventType": latest_event.event_type,
                    "message": latest_event.message,
                    "createdAt": latest_event.created_at.isoformat(),
                }
                if latest_event
                else None
            ),
            "artifacts": [
                {
                    "type": artifact.artifact_type,
                    "version": artifact.artifact_version,
                    "producedAt": artifact.produced_at.isoformat(),
                    "payloadKeys": sorted(list(artifact.payload.keys()))
                    if isinstance(artifact.payload, dict)
                    else [],
                }
                for artifact in artifacts
            ],
            "artifactTypeSet": sorted({artifact.artifact_type for artifact in artifacts}),
            "snapshot": (
                {
                    "symbol": snapshot.symbol,
                    "latestWorkflowId": snapshot.latest_workflow_id,
                    "state": snapshot.state,
                    "summaryIsNull": summary is None,
                    "detailsIsNull": details is None,
                    "modelMetadataIsNull": model_metadata is None,
                    "hasStructuredOutput": isinstance(details.get("structuredOutput"), dict)
                    if isinstance(details, dict)
                    else False,
                    "updatedAt": snapshot.updated_at.isoformat(),
                }
                if snapshot is not None
                else None
            ),
            "classification": {
                "isTerminal": workflow.state in {"completed", "completed_cached", "failed", "cancelled"},
                "hasArtifacts": len(artifacts) > 0,
                "artifactCount": len(artifacts),
                "suspectExecutionStall": workflow.state == "running" and len(artifacts) == 0,
                "suspectProjectionOverwrite": len(artifacts) > 0 and snapshot is not None and details is None,
            },
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

    return router
