from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow.types import Transition, WorkflowState
from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_workflow_artifact import AnalysisWorkflowArtifact
from app.models.workflow.analysis_workflow_event import AnalysisWorkflowEvent
from app.workflows.analysis.projections.store import upsert_workflow_projection
from app.workflows.analysis.sse import SseBroker


class WorkflowRuntime:
    def __init__(self, sse_broker: SseBroker) -> None:
        self._sse_broker = sse_broker

    async def emit(
        self,
        db: AsyncSession,
        workflow: AnalysisWorkflow,
        state: WorkflowState,
        substate: str | None,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        workflow.state = state.value
        workflow.substate = substate
        event = AnalysisWorkflowEvent(
            workflow_id=workflow.id,
            state=state.value,
            substate=substate,
            message=message,
            payload=payload,
        )
        db.add(event)
        await upsert_workflow_projection(
            db,
            workflow,
            message=message,
            latest_event_at=datetime.now(timezone.utc),
        )
        await db.commit()
        await self._sse_broker.publish(
            Transition(
                workflow_id=workflow.id,
                symbol=workflow.symbol,
                state=state,
                substate=substate,
                message=message,
                payload=payload,
            )
        )

    async def persist_artifact(
        self,
        db: AsyncSession,
        workflow_id: str,
        artifact_type: str,
        payload: dict[str, Any],
        artifact_version: str = "v1",
    ) -> None:
        db.add(
            AnalysisWorkflowArtifact(
                workflow_id=workflow_id,
                artifact_type=artifact_type,
                artifact_version=artifact_version,
                payload=payload,
            )
        )
        result = await db.execute(
            select(AnalysisWorkflow).where(AnalysisWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if workflow is None:
            return
        await upsert_workflow_projection(
            db,
            workflow,
            artifact_type=artifact_type,
            artifact_payload=payload,
        )
