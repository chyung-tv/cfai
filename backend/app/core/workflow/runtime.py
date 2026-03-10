from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow.types import Transition, WorkflowState
from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_workflow_artifact import AnalysisWorkflowArtifact
from app.models.workflow.analysis_workflow_event import AnalysisWorkflowEvent
from app.workflows.analysis.projections.store import upsert_workflow_projection
from app.workflows.analysis.sse import SseBroker


class WorkflowRuntime:
    _ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        WorkflowState.queued.value: {
            WorkflowState.queued.value,
            WorkflowState.running.value,
            WorkflowState.failed.value,
            WorkflowState.cancelled.value,
        },
        WorkflowState.running.value: {
            WorkflowState.running.value,
            WorkflowState.completed.value,
            WorkflowState.completed_cached.value,
            WorkflowState.failed.value,
            WorkflowState.cancelled.value,
        },
        WorkflowState.completed.value: set(),
        WorkflowState.completed_cached.value: set(),
        WorkflowState.failed.value: set(),
        WorkflowState.cancelled.value: set(),
    }

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
        self._validate_transition(workflow.state, state.value)
        workflow.state = state.value
        workflow.substate = substate
        if state in {WorkflowState.completed, WorkflowState.completed_cached}:
            workflow.completed_at = datetime.now(timezone.utc)
            workflow.failed_at = None
            workflow.error_code = None
        if state == WorkflowState.failed:
            workflow.failed_at = datetime.now(timezone.utc)
        event_seq = await self._next_event_seq(db=db, workflow_id=workflow.id)
        event = AnalysisWorkflowEvent(
            workflow_id=workflow.id,
            seq_no=event_seq,
            state=state.value,
            substate=substate,
            event_type="transition",
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

    async def fail(
        self,
        db: AsyncSession,
        workflow: AnalysisWorkflow,
        *,
        substate: str = "failed",
        message: str,
        error_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        workflow.error_code = error_code
        await self.emit(
            db=db,
            workflow=workflow,
            state=WorkflowState.failed,
            substate=substate,
            message=message,
            payload=payload,
        )

    async def persist_artifact(
        self,
        db: AsyncSession,
        workflow_id: str,
        artifact_type: str,
        payload: dict[str, Any],
        artifact_version: str = "v1",
    ) -> None:
        existing_result = await db.execute(
            select(AnalysisWorkflowArtifact).where(
                AnalysisWorkflowArtifact.workflow_id == workflow_id,
                AnalysisWorkflowArtifact.artifact_type == artifact_type,
                AnalysisWorkflowArtifact.artifact_version == artifact_version,
            )
        )
        artifact = existing_result.scalar_one_or_none()
        if artifact is None:
            artifact = AnalysisWorkflowArtifact(
                workflow_id=workflow_id,
                artifact_type=artifact_type,
                artifact_version=artifact_version,
                payload=payload,
            )
        else:
            artifact.payload = payload
        db.add(artifact)
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

    @classmethod
    def _validate_transition(cls, previous_state: str, next_state: str) -> None:
        allowed = cls._ALLOWED_TRANSITIONS.get(previous_state, set())
        if next_state not in allowed:
            raise RuntimeError(f"invalid_state_transition:{previous_state}->{next_state}")

    async def _next_event_seq(self, *, db: AsyncSession, workflow_id: str) -> int:
        result = await db.execute(
            select(func.max(AnalysisWorkflowEvent.seq_no)).where(
                AnalysisWorkflowEvent.workflow_id == workflow_id
            )
        )
        current = result.scalar_one_or_none()
        return int(current or 0) + 1
