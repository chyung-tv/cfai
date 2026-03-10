from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
import copy
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.workflow.analysis_candidate_card import AnalysisCandidateCard
from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_workflow_event import AnalysisWorkflowEvent
from app.models.workflow.analysis_symbol_snapshot import AnalysisSymbolSnapshot
from app.workflows.analysis.orchestrator import WorkflowOrchestrator
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
        limit: int = Query(default=100, ge=1, le=500),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        result = await db.execute(
            select(AnalysisCandidateCard)
            .order_by(
                desc(AnalysisCandidateCard.quality_score),
                desc(AnalysisCandidateCard.freshness_updated_at),
            )
            .limit(limit)
        )
        rows = result.scalars().all()
        return {
            "cards": [
                {
                    "symbol": row.symbol,
                    "qualityScore": row.quality_score,
                    "valuationSignal": row.valuation_signal,
                    "recentChangeSignal": row.recent_change_signal,
                    "portfolioImpactSignal": row.portfolio_impact_signal,
                    "freshnessUpdatedAt": row.freshness_updated_at.isoformat()
                    if row.freshness_updated_at
                    else None,
                    "freshnessExpiresAt": row.freshness_expires_at.isoformat()
                    if row.freshness_expires_at
                    else None,
                    "payload": row.card_payload,
                }
                for row in rows
            ]
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
