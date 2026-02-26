from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_workflow import AnalysisWorkflow
from app.models.analysis_workflow_event import AnalysisWorkflowEvent
from app.workflow.nodes.execute_placeholder import ExecutePlaceholderNode
from app.workflow.nodes.publish_sse import PublishSseNode
from app.workflow.nodes.resolve_cache import ResolveCacheNode
from app.workflow.nodes.validate_input import ValidateInputNode
from app.workflow.sse import SseBroker
from app.workflow.types import Transition, WorkflowState


class WorkflowOrchestrator:
    def __init__(self, sse_broker: SseBroker) -> None:
        self._sse_broker = sse_broker
        self._tasks: set[asyncio.Task] = set()

    def _track_task(self, task: asyncio.Task) -> None:
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def start_workflow(
        self,
        db: AsyncSession,
        symbol: str,
        force_refresh: bool,
        user_id: int | None,
    ) -> str:
        workflow_id = str(uuid4())
        workflow = AnalysisWorkflow(
            id=workflow_id,
            user_id=user_id,
            symbol=symbol.strip().upper(),
            state=WorkflowState.queued.value,
            substate=None,
            force_refresh=force_refresh,
        )
        db.add(workflow)
        await db.commit()

        await self._emit(
            db,
            workflow,
            WorkflowState.queued,
            "queued",
            "Analysis queued",
            {"forceRefresh": force_refresh},
        )

        task = asyncio.create_task(self._run_workflow(workflow_id))
        self._track_task(task)
        return workflow_id

    async def _run_workflow(self, workflow_id: str) -> None:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AnalysisWorkflow).where(AnalysisWorkflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if workflow is None:
                return

            context: dict[str, Any] = {
                "workflow_id": workflow.id,
                "symbol": workflow.symbol,
                "force_refresh": workflow.force_refresh,
            }
            try:
                await self._emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "validate_input",
                    "Validating input",
                )
                await ValidateInputNode().execute(context)

                await self._emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "resolve_cache",
                    "Resolving cache",
                )
                cache_result = await ResolveCacheNode().execute(context)
                if cache_result.get("cache_hit"):
                    await self._emit(
                        db,
                        workflow,
                        WorkflowState.completed_cached,
                        "resolve_cache",
                        "Completed from cache",
                        {"result": context.get("cached_result")},
                    )
                    workflow.result_payload = context.get("cached_result")
                    await db.commit()
                    return

                await self._emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "assemble_result",
                    "Generating placeholder analysis result",
                )
                output = await ExecutePlaceholderNode().execute(context)
                workflow.result_payload = output.get("result")
                await db.commit()

                await self._emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "publish_sse",
                    "Publishing workflow completion",
                )
                await PublishSseNode().execute(context)

                await self._emit(
                    db,
                    workflow,
                    WorkflowState.completed,
                    "completed",
                    "Analysis completed",
                    {"result": workflow.result_payload},
                )
            except Exception as exc:
                workflow.error_message = str(exc)
                await db.commit()
                await self._emit(
                    db,
                    workflow,
                    WorkflowState.failed,
                    "failed",
                    "Analysis failed",
                    {"error": str(exc)},
                )

    async def _emit(
        self,
        db: AsyncSession,
        workflow: AnalysisWorkflow,
        state: WorkflowState,
        substate: str | None,
        message: str,
        payload: dict | None = None,
    ) -> None:
        workflow.state = state.value
        workflow.substate = substate
        db.add(
            AnalysisWorkflowEvent(
                workflow_id=workflow.id,
                state=state.value,
                substate=substate,
                message=message,
                payload=payload,
            )
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
