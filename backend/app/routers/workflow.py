from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import require_auth
from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_workflow_event import AnalysisWorkflowEvent
from app.models.workflow.analysis_workflow_projection import AnalysisWorkflowProjection
from app.models.user import User
from app.workflows.analysis.projections.store import upsert_workflow_projection
from app.workflows.analysis.orchestrator import WorkflowOrchestrator
from app.workflows.analysis.sse import SseBroker


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
        current_user: User = Depends(require_auth),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, str]:
        symbol = body.symbol.strip().upper()
        if not symbol:
            raise HTTPException(status_code=400, detail="symbol is required")
        workflow_id = await orchestrator.start_workflow(
            db=db,
            symbol=symbol,
            force_refresh=force,
            user_id=current_user.id,
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
                    "id": event.workflow_id,
                    "state": event.state,
                    "substate": event.substate,
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
            select(AnalysisWorkflowProjection)
            .where(
                AnalysisWorkflowProjection.symbol == symbol,
                AnalysisWorkflowProjection.state.in_(["completed", "completed_cached"]),
            )
            .order_by(desc(AnalysisWorkflowProjection.updated_at))
            .limit(1)
        )
        projection = result.scalar_one_or_none()
        if projection is not None:
            return projection.result_payload

        # Backward-compatible fallback for rows created before projection table rollout.
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
        return workflow.result_payload

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
                "analysisResult": item.result_payload,
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
        result = await db.execute(select(AnalysisWorkflow).where(AnalysisWorkflow.id == query_id))
        workflow = result.scalar_one_or_none()
        if workflow is None:
            raise HTTPException(status_code=404, detail="query not found")
        workflow.state = "failed"
        workflow.substate = "failed"
        db.add(
            AnalysisWorkflowEvent(
                workflow_id=workflow.id,
                state="failed",
                substate="failed",
                message="Marked failed manually",
                payload=None,
            )
        )
        await upsert_workflow_projection(db, workflow, message="Marked failed manually")
        await db.commit()
        return {"status": "failed"}

    return router
