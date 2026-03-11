from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.workflow.runtime import WorkflowRuntime
from app.core.workflow.types import WorkflowState
from app.models.workflow.analysis_workflow import AnalysisWorkflow
from app.models.workflow.analysis_workflow_event import AnalysisWorkflowEvent
from app.models.workflow.analysis_symbol_snapshot import AnalysisSymbolSnapshot
from app.providers.advisor_client import AdvisorClient
from app.providers.fmp_client import FmpClient
from app.providers.gemini_deep_research import GeminiDeepResearchClient
from app.workflows.analysis.context import WorkflowContext
from app.workflows.analysis.nodes.advisor_decision import AdvisorDecisionNode
from app.workflows.analysis.nodes.audit_growth_likelihood import (
    AuditGrowthLikelihoodNode,
)
from app.workflows.analysis.nodes.deep_research import DeepResearchNode
from app.workflows.analysis.nodes.publish_sse import PublishSseNode
from app.workflows.analysis.nodes.resolve_cache import ResolveCacheNode
from app.workflows.analysis.nodes.resolve_query import ResolveQueryNode
from app.workflows.analysis.nodes.reverse_dcf import ReverseDcfNode
from app.workflows.analysis.nodes.structured_output import StructuredOutputNode
from app.workflows.analysis.nodes.validate_input import ValidateInputNode
from app.workflows.analysis.projections.store import upsert_workflow_projection
from app.workflows.analysis.sse import SseBroker

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    def __init__(
        self,
        sse_broker: SseBroker,
        deep_research_client: GeminiDeepResearchClient,
        fmp_client: FmpClient,
        advisor_client: AdvisorClient,
    ) -> None:
        self._deep_research_client = deep_research_client
        self._fmp_client = fmp_client
        self._advisor_client = advisor_client
        self._runtime = WorkflowRuntime(sse_broker)
        self._tasks: set[asyncio.Task] = set()
        self._stall_signaled_at: dict[str, datetime] = {}
        self._monitor_task: asyncio.Task | None = None
        self._start_stall_monitor()

    def _track_task(self, task: asyncio.Task) -> None:
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def _start_stall_monitor(self) -> None:
        if self._monitor_task is not None and not self._monitor_task.done():
            return
        self._monitor_task = asyncio.create_task(self._monitor_running_workflows())

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

        await self._runtime.emit(
            db,
            workflow,
            WorkflowState.queued,
            "queued",
            "Analysis queued",
            {"forceRefresh": force_refresh},
        )
        logger.info(
            "workflow_started trace_id=%s symbol=%s force_refresh=%s",
            workflow.id,
            workflow.symbol,
            workflow.force_refresh,
        )

        task = asyncio.create_task(self._run_workflow(workflow_id))
        self._track_task(task)
        return workflow_id

    async def mark_workflow_failed(self, db: AsyncSession, workflow_id: str) -> bool:
        result = await db.execute(select(AnalysisWorkflow).where(AnalysisWorkflow.id == workflow_id))
        workflow = result.scalar_one_or_none()
        if workflow is None:
            return False
        await self._runtime.fail(
            db=db,
            workflow=workflow,
            substate="failed",
            message="Marked failed manually",
            error_code="manual_failure",
            payload=None,
        )
        return True

    async def _run_workflow(self, workflow_id: str) -> None:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AnalysisWorkflow).where(AnalysisWorkflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if workflow is None:
                return

            context: WorkflowContext = {
                "workflow_id": workflow.id,
                "symbol": workflow.symbol,
                "force_refresh": workflow.force_refresh,
                "db": db,
            }
            try:
                await self._run_node_step(
                    db=db,
                    workflow=workflow,
                    context=context,
                    node=ValidateInputNode(),
                    substate="validate_input",
                    transition_message="Validating input",
                )

                await self._run_node_step(
                    db=db,
                    workflow=workflow,
                    context=context,
                    node=ResolveQueryNode(),
                    substate="resolve_query",
                    transition_message="Resolving query to catalog symbol",
                )
                workflow.symbol = context["symbol"]
                workflow.catalog_id = context.get("catalog_id")
                await db.commit()

                await self._hydrate_cached_result(db=db, workflow=workflow, context=context)
                cache_result = await self._run_node_step(
                    db=db,
                    workflow=workflow,
                    context=context,
                    node=ResolveCacheNode(),
                    substate="resolve_cache",
                    transition_message="Resolving cache",
                )
                if cache_result.get("cache_hit"):
                    await self._runtime.emit(
                        db,
                        workflow,
                        WorkflowState.completed_cached,
                        "resolve_cache",
                        "Completed from cache",
                        {"cacheHit": True},
                    )
                    cached_result = context.get("cached_result")
                    if isinstance(cached_result, dict):
                        await self._runtime.persist_artifact(
                            db,
                            workflow.id,
                            "final_result",
                            cached_result,
                            artifact_version="v1-cached",
                        )
                        await upsert_workflow_projection(db, workflow, message="Completed from cache")
                    await db.commit()
                    return

                await self._run_deep_research(db, workflow, context)

                output = await self._run_node_step(
                    db=db,
                    workflow=workflow,
                    context=context,
                    node=StructuredOutputNode(self._deep_research_client),
                    substate="structured_output",
                    transition_message="Structuring deep research output",
                )
                await upsert_workflow_projection(db, workflow, message="Structured output persisted")
                await self._runtime.persist_artifact(
                    db,
                    workflow.id,
                    "structured_output",
                    output["structuredOutput"],
                )
                await db.commit()

                output = await self._run_node_step(
                    db=db,
                    workflow=workflow,
                    context=context,
                    node=ReverseDcfNode(self._fmp_client),
                    substate="reverse_dcf",
                    transition_message="Running reverse DCF calculation",
                )
                await upsert_workflow_projection(db, workflow, message="Reverse DCF persisted")
                await self._runtime.persist_artifact(
                    db,
                    workflow.id,
                    "reverse_dcf",
                    output["reverseDcf"],
                )
                await db.commit()

                output = await self._run_node_step(
                    db=db,
                    workflow=workflow,
                    context=context,
                    node=AuditGrowthLikelihoodNode(self._deep_research_client),
                    substate="audit_growth_likelihood",
                    transition_message="Auditing growth likelihood against deep research evidence",
                )
                await upsert_workflow_projection(
                    db, workflow, message="Audit growth likelihood persisted"
                )
                await self._runtime.persist_artifact(
                    db,
                    workflow.id,
                    "audit_growth_likelihood",
                    output["auditGrowthLikelihood"],
                )
                await db.commit()

                output = await self._run_node_step(
                    db=db,
                    workflow=workflow,
                    context=context,
                    node=AdvisorDecisionNode(self._advisor_client),
                    substate="advisor_decision",
                    transition_message="Generating investor-profile advisor actions",
                )
                await upsert_workflow_projection(db, workflow, message="Advisor decision persisted")
                await self._runtime.persist_artifact(
                    db,
                    workflow.id,
                    "advisor_decision",
                    output["advisorDecision"],
                )
                await db.commit()

                await self._run_node_step(
                    db=db,
                    workflow=workflow,
                    context=context,
                    node=PublishSseNode(),
                    substate="publish_sse",
                    transition_message="Publishing workflow completion",
                )

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.completed,
                    "completed",
                    "Analysis completed",
                    {"hasResult": True},
                )
            except Exception as exc:
                await self._fail_workflow_isolated(
                    workflow_id=workflow.id,
                    error=str(exc),
                )
                logger.exception(
                    "workflow_failed trace_id=%s symbol=%s substate=%s",
                    workflow.id,
                    workflow.symbol,
                    workflow.substate,
                )

    async def _run_node_step(
        self,
        *,
        db: AsyncSession,
        workflow: AnalysisWorkflow,
        context: WorkflowContext,
        node: Any,
        substate: str,
        transition_message: str,
    ) -> dict[str, Any]:
        await self._runtime.emit(
            db,
            workflow,
            WorkflowState.running,
            substate,
            transition_message,
        )
        started_at = datetime.now(timezone.utc)
        await self._emit_progress_isolated(
            workflow_id=workflow.id,
            event_type="node_started",
            substate=substate,
            message=f"{substate} started",
            payload={
                "node": substate,
                "startedAt": started_at.isoformat(),
            },
        )
        logger.info(
            "workflow_node_started trace_id=%s symbol=%s node=%s",
            workflow.id,
            workflow.symbol,
            substate,
        )
        interval_seconds = max(1, settings.workflow_node_heartbeat_interval_seconds)
        node_task = asyncio.create_task(node.execute(context))
        try:
            while True:
                try:
                    output = await asyncio.wait_for(asyncio.shield(node_task), timeout=interval_seconds)
                    break
                except TimeoutError as exc:
                    if node_task.done():
                        raise exc
                    elapsed_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
                    await self._emit_progress_isolated(
                        workflow_id=workflow.id,
                        event_type="node_heartbeat",
                        substate=substate,
                        message=f"{substate} still running",
                        payload={"node": substate, "elapsedMs": elapsed_ms},
                    )
                    logger.info(
                        "workflow_node_heartbeat trace_id=%s symbol=%s node=%s elapsed_ms=%s",
                        workflow.id,
                        workflow.symbol,
                        substate,
                        elapsed_ms,
                    )
        except TimeoutError as exc:
            duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
            await self._emit_progress_isolated(
                workflow_id=workflow.id,
                event_type="node_timeout",
                substate=substate,
                message=f"{substate} timed out",
                payload={
                    "node": substate,
                    "durationMs": duration_ms,
                    "errorType": type(exc).__name__,
                },
            )
            logger.warning(
                "workflow_node_timeout trace_id=%s symbol=%s node=%s duration_ms=%s",
                workflow.id,
                workflow.symbol,
                substate,
                duration_ms,
            )
            raise
        except Exception as exc:
            duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
            await self._emit_progress_isolated(
                workflow_id=workflow.id,
                event_type="node_failed",
                substate=substate,
                message=f"{substate} failed",
                payload={
                    "node": substate,
                    "durationMs": duration_ms,
                    "errorType": type(exc).__name__,
                    "error": str(exc)[:300],
                },
            )
            logger.exception(
                "workflow_node_failed trace_id=%s symbol=%s node=%s duration_ms=%s",
                workflow.id,
                workflow.symbol,
                substate,
                duration_ms,
            )
            raise
        duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
        await self._emit_progress_isolated(
            workflow_id=workflow.id,
            event_type="node_succeeded",
            substate=substate,
            message=f"{substate} completed",
            payload={"node": substate, "durationMs": duration_ms},
        )
        logger.info(
            "workflow_node_succeeded trace_id=%s symbol=%s node=%s duration_ms=%s",
            workflow.id,
            workflow.symbol,
            substate,
            duration_ms,
        )
        return output

    async def _emit_progress_isolated(
        self,
        *,
        workflow_id: str,
        event_type: str,
        substate: str | None,
        message: str,
        payload: dict[str, Any] | None,
    ) -> None:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as isolated_db:
            result = await isolated_db.execute(
                select(AnalysisWorkflow).where(AnalysisWorkflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if workflow is None:
                return
            await self._runtime.emit_progress(
                isolated_db,
                workflow,
                event_type=event_type,
                substate=substate,
                message=message,
                payload=payload,
            )

    async def _fail_workflow_isolated(self, *, workflow_id: str, error: str) -> None:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as isolated_db:
            result = await isolated_db.execute(
                select(AnalysisWorkflow).where(AnalysisWorkflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if workflow is None:
                return
            workflow.error_message = error[:500]
            workflow.error_code = "analysis_failed"
            await isolated_db.commit()
            await self._runtime.fail(
                isolated_db,
                workflow,
                substate="failed",
                message="Analysis failed",
                error_code="analysis_failed",
                payload={"error": error},
            )

    async def _run_deep_research(
        self,
        db: AsyncSession,
        workflow: AnalysisWorkflow,
        context: WorkflowContext,
    ) -> None:
        if settings.skip_deep_research_in_tests:
            seeded = await self._seed_report_from_latest(db, context["symbol"])
            if seeded is not None:
                context["result"] = seeded
                context["report_markdown"] = seeded["reportMarkdown"]
                citations = seeded.get("citations")
                if isinstance(citations, list):
                    context["report_citations"] = citations
                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "deep_research_skipped_fixture",
                    "Skipped deep research with fixture payload",
                )
                await self._runtime.persist_artifact(
                    db,
                    workflow.id,
                    "deep_research_fixture",
                    seeded,
                    artifact_version="v1-test-skip",
                )
                return

        await self._run_node_step(
            db=db,
            workflow=workflow,
            context=context,
            node=DeepResearchNode(self._deep_research_client),
            substate="deep_research",
            transition_message="Running deep research analysis",
        )
        deep_research_result = context.get("result")
        if isinstance(deep_research_result, dict):
            await self._runtime.persist_artifact(
                db,
                workflow.id,
                "deep_research",
                deep_research_result,
            )

    async def _seed_report_from_latest(self, db: AsyncSession, symbol: str) -> dict[str, Any] | None:
        latest_result = await db.execute(
            select(AnalysisSymbolSnapshot)
            .where(
                AnalysisSymbolSnapshot.symbol == symbol,
                AnalysisSymbolSnapshot.state.in_(["completed", "completed_cached"]),
            )
            .order_by(desc(AnalysisSymbolSnapshot.updated_at))
            .limit(1)
        )
        latest = latest_result.scalar_one_or_none()
        payload = latest.details if latest is not None and isinstance(latest.details, dict) else None
        if not isinstance(payload, dict):
            return None
        report_markdown = payload.get("reportMarkdown")
        if not isinstance(report_markdown, str) or not report_markdown.strip():
            return None
        seeded: dict[str, Any] = {
            "id": payload.get("id") or str(uuid4()),
            "symbol": payload.get("symbol") or symbol,
            "reportMarkdown": report_markdown,
            "citations": payload.get("citations") if isinstance(payload.get("citations"), list) else [],
            "interactionId": payload.get("interactionId") or "fixture-seeded",
            "generatedAt": payload.get("generatedAt"),
            "modelMetadata": payload.get("modelMetadata")
            if isinstance(payload.get("modelMetadata"), dict)
            else {},
        }
        return seeded

    async def _hydrate_cached_result(
        self,
        *,
        db: AsyncSession,
        workflow: AnalysisWorkflow,
        context: WorkflowContext,
    ) -> None:
        if workflow.force_refresh:
            return
        result = await db.execute(
            select(AnalysisSymbolSnapshot).where(
                AnalysisSymbolSnapshot.symbol == workflow.symbol,
                AnalysisSymbolSnapshot.state.in_(["completed", "completed_cached"]),
            )
        )
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            return
        if snapshot.freshness_expires_at and snapshot.freshness_expires_at < datetime.now(timezone.utc):
            return
        details = snapshot.details if isinstance(snapshot.details, dict) else {}
        summary = snapshot.summary if isinstance(snapshot.summary, dict) else {}
        context["cached_result"] = {
            "id": workflow.id,
            "symbol": workflow.symbol,
            "summary": summary,
            "details": details,
            "modelMetadata": snapshot.model_metadata if isinstance(snapshot.model_metadata, dict) else {},
            "reportMarkdown": details.get("reportMarkdown"),
            "citations": details.get("citations", []),
        }

    async def _monitor_running_workflows(self) -> None:
        from app.db.session import AsyncSessionLocal

        interval_seconds = max(5, settings.workflow_stall_monitor_interval_seconds)
        stale_threshold_seconds = max(10, settings.workflow_stale_progress_threshold_seconds)
        cooldown_seconds = max(30, settings.workflow_stall_signal_cooldown_seconds)
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(AnalysisWorkflow).where(AnalysisWorkflow.state == WorkflowState.running.value)
                    )
                    running_workflows = result.scalars().all()
                    now = datetime.now(timezone.utc)
                    active_ids = {workflow.id for workflow in running_workflows}
                    stale_ids = set(self._stall_signaled_at.keys()) - active_ids
                    for workflow_id in stale_ids:
                        self._stall_signaled_at.pop(workflow_id, None)

                    for workflow in running_workflows:
                        event_result = await db.execute(
                            select(AnalysisWorkflowEvent)
                            .where(AnalysisWorkflowEvent.workflow_id == workflow.id)
                            .order_by(desc(AnalysisWorkflowEvent.created_at))
                            .limit(1)
                        )
                        last_event = event_result.scalar_one_or_none()
                        if last_event is None:
                            continue
                        elapsed_seconds = (now - last_event.created_at).total_seconds()
                        if elapsed_seconds < stale_threshold_seconds:
                            continue
                        last_signaled_at = self._stall_signaled_at.get(workflow.id)
                        if (
                            last_signaled_at is not None
                            and (now - last_signaled_at).total_seconds() < cooldown_seconds
                        ):
                            continue
                        await self._runtime.emit_progress(
                            db,
                            workflow,
                            event_type="stalled_no_progress",
                            substate=workflow.substate,
                            message="Workflow has no progress beyond stale threshold",
                            payload={
                                "node": workflow.substate,
                                "lastEventAt": last_event.created_at.isoformat(),
                                "elapsedWithoutProgressSec": int(elapsed_seconds),
                                "staleThresholdSec": stale_threshold_seconds,
                            },
                        )
                        self._stall_signaled_at[workflow.id] = now
                        logger.warning(
                            "workflow_stalled_no_progress trace_id=%s symbol=%s node=%s elapsed_without_progress_sec=%s",
                            workflow.id,
                            workflow.symbol,
                            workflow.substate,
                            int(elapsed_seconds),
                        )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("workflow_stall_monitor_error")
            await asyncio.sleep(interval_seconds)


__all__ = ["WorkflowOrchestrator"]
