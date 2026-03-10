from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.workflow.runtime import WorkflowRuntime
from app.core.workflow.types import WorkflowState
from app.models.workflow.analysis_workflow import AnalysisWorkflow
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

        await self._runtime.emit(
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
                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "validate_input",
                    "Validating input",
                )
                await ValidateInputNode().execute(context)

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "resolve_query",
                    "Resolving query to catalog symbol",
                )
                await ResolveQueryNode().execute(context)
                workflow.symbol = context["symbol"]
                workflow.catalog_id = context.get("catalog_id")
                await db.commit()

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "resolve_cache",
                    "Resolving cache",
                )
                await self._hydrate_cached_result(db=db, workflow=workflow, context=context)
                cache_result = await ResolveCacheNode().execute(context)
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

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "structured_output",
                    "Structuring deep research output",
                )
                output = await StructuredOutputNode(self._deep_research_client).execute(context)
                await upsert_workflow_projection(db, workflow, message="Structured output persisted")
                await self._runtime.persist_artifact(
                    db,
                    workflow.id,
                    "structured_output",
                    output["structuredOutput"],
                )
                await db.commit()

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "reverse_dcf",
                    "Running reverse DCF calculation",
                )
                output = await ReverseDcfNode(self._fmp_client).execute(context)
                await upsert_workflow_projection(db, workflow, message="Reverse DCF persisted")
                await self._runtime.persist_artifact(
                    db,
                    workflow.id,
                    "reverse_dcf",
                    output["reverseDcf"],
                )
                await db.commit()

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "audit_growth_likelihood",
                    "Auditing growth likelihood against deep research evidence",
                )
                output = await AuditGrowthLikelihoodNode(self._deep_research_client).execute(context)
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

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "advisor_decision",
                    "Generating investor-profile advisor actions",
                )
                output = await AdvisorDecisionNode(self._advisor_client).execute(context)
                await upsert_workflow_projection(db, workflow, message="Advisor decision persisted")
                await self._runtime.persist_artifact(
                    db,
                    workflow.id,
                    "advisor_decision",
                    output["advisorDecision"],
                )
                await db.commit()

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.running,
                    "publish_sse",
                    "Publishing workflow completion",
                )
                await PublishSseNode().execute(context)

                await self._runtime.emit(
                    db,
                    workflow,
                    WorkflowState.completed,
                    "completed",
                    "Analysis completed",
                    {"hasResult": True},
                )
            except Exception as exc:
                # Keep DB writes safe: error_message column is VARCHAR(500).
                workflow.error_message = str(exc)[:500]
                workflow.error_code = "analysis_failed"
                await db.commit()
                await self._runtime.fail(
                    db,
                    workflow,
                    substate="failed",
                    message="Analysis failed",
                    error_code="analysis_failed",
                    payload={"error": str(exc)},
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

        await self._runtime.emit(
            db,
            workflow,
            WorkflowState.running,
            "deep_research",
            "Running deep research analysis",
        )
        await DeepResearchNode(self._deep_research_client).execute(context)
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


__all__ = ["WorkflowOrchestrator"]
