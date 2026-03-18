from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runtime.engine import AgentRuntime
from app.agent.runtime.event_stream import to_sse
from app.agent.runtime.turn_context import AgentMessage, AgentTurnContext
from app.agent.skills.registry import SkillRegistry
from app.core.config import settings
from app.copilot.service.memory_jobs import MemoryJob, MemoryJobRunner
from app.copilot.service.memory_service import MemoryService
from app.copilot.service.notification_broker import NotificationBroker
from app.copilot.service.workspace_service import CopilotWorkspaceService
from app.db.session import get_db


class WorkspaceQuery(BaseModel):
    threadId: str | None = None


class ChatTurnBody(BaseModel):
    threadId: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class AddRuleBody(BaseModel):
    ruleText: str = Field(min_length=1, max_length=2000)


class UpdateRuleBody(BaseModel):
    ruleText: str = Field(min_length=1, max_length=2000)
    isActive: bool = True


class CreateThreadBody(BaseModel):
    title: str | None = Field(default=None, max_length=160)


class CreateDocumentBody(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    docKey: str | None = Field(default=None, max_length=64)
    initialContent: str | None = Field(default=None, max_length=200_000)


class UpdateDocumentBody(BaseModel):
    content: str = Field(min_length=1, max_length=200_000)


class CheckpointBody(BaseModel):
    message: str | None = Field(default=None, max_length=300)


class RevisionListBody(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)


class RevertBody(BaseModel):
    revisionId: str = Field(min_length=1, max_length=36)
    message: str | None = Field(default=None, max_length=300)


class WorkspaceSnapshotCreateBody(BaseModel):
    message: str | None = Field(default=None, max_length=300)


class WorkspaceSnapshotListBody(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)


class WorkspaceSnapshotRestoreBody(BaseModel):
    message: str | None = Field(default=None, max_length=300)


class UpdateSkillBody(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    brief: str = Field(default="", max_length=2000)
    prompt: str = Field(default="", max_length=20000)
    enabled: bool = True
    allowedTools: list[str] = Field(default_factory=list)
    requiredOrder: list[str] = Field(default_factory=list)
    blockedCombinations: list[list[str]] = Field(default_factory=list)


class UpdateMemoryBody(BaseModel):
    key: str = Field(min_length=1, max_length=160)
    value: str = Field(default="", max_length=10000)
    type: str = Field(min_length=1, max_length=40)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(default="", max_length=2000)


class UpdateMemorySummaryBody(BaseModel):
    summary: str = Field(default="", max_length=10000)


def _serialize_skill_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id"),
        "name": entry.get("name"),
        "brief": entry.get("brief"),
        "enabled": bool(entry.get("enabled", False)),
        "allowedTools": list(entry.get("allowedTools") or []),
    }


def _resolve_user_id(request: Request | None) -> str:
    if request is None:
        return settings.memory_default_user_id
    query_user_id = (request.query_params.get("userId") or "").strip()
    if query_user_id:
        return query_user_id
    header_user_id = (request.headers.get("x-user-id") or "").strip()
    return header_user_id or settings.memory_default_user_id


def create_copilot_router(
    service: CopilotWorkspaceService,
    runtime: AgentRuntime,
    skill_registry: SkillRegistry,
    memory_service: MemoryService,
    memory_jobs: MemoryJobRunner,
    broker: NotificationBroker,
) -> APIRouter:
    router = APIRouter(prefix="/copilot", tags=["copilot"])

    @router.post("/workspace")
    async def get_workspace(
        body: WorkspaceQuery,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        await service.ensure_workspace_state(db)
        thread = await service.get_or_create_thread(db, body.threadId)
        threads = await service.list_threads(db)
        messages = await service.list_messages(db, thread.id)
        rules = await service.list_rules(db)
        documents = await service.list_documents(db)
        heads = await service.get_document_heads(db, doc_keys=[doc.doc_key for doc in documents])
        await db.commit()
        return {
            "userId": user_id,
            "thread": {"id": thread.id, "title": thread.title},
            "threads": [
                {
                    "id": item.id,
                    "title": item.title,
                    "createdAt": item.created_at.isoformat(),
                    "updatedAt": item.updated_at.isoformat(),
                }
                for item in threads
            ],
            "documents": [service.serialize_document(doc=doc, head=heads.get(doc.doc_key)) for doc in documents],
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "createdAt": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
            "rules": [
                {
                    "id": rule.id,
                    "ruleText": rule.rule_text,
                    "createdAt": rule.created_at.isoformat(),
                }
                for rule in rules
            ],
        }

    @router.post("/workspace/snapshots")
    async def create_workspace_snapshot(
        body: WorkspaceSnapshotCreateBody,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        snapshot = await service.create_workspace_snapshot(
            db,
            user_id=user_id,
            message=(body.message or "Workspace snapshot").strip(),
            author_type="user",
        )
        await db.commit()
        return {
            "snapshot": {
                "id": snapshot.id,
                "userId": snapshot.user_id,
                "parentSnapshotId": snapshot.parent_snapshot_id,
                "message": snapshot.message,
                "authorType": snapshot.author_type,
                "createdAt": snapshot.created_at.isoformat(),
            }
        }

    @router.post("/workspace/snapshots/list")
    async def list_workspace_snapshots(
        body: WorkspaceSnapshotListBody,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        snapshots = await service.list_workspace_snapshots(db, user_id=user_id, limit=body.limit)
        await db.commit()
        return {
            "snapshots": [
                {
                    "id": row.id,
                    "userId": row.user_id,
                    "parentSnapshotId": row.parent_snapshot_id,
                    "message": row.message,
                    "authorType": row.author_type,
                    "createdAt": row.created_at.isoformat(),
                }
                for row in snapshots
            ]
        }

    @router.post("/workspace/snapshots/{snapshot_id}/restore")
    async def restore_workspace_snapshot(
        snapshot_id: str,
        body: WorkspaceSnapshotRestoreBody,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        try:
            snapshot = await service.restore_workspace_snapshot(
                db,
                user_id=user_id,
                snapshot_id=snapshot_id,
                message=(body.message or f"Restore snapshot {snapshot_id}").strip(),
                author_type="user",
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="snapshot not found") from exc
        await db.commit()
        return {
            "snapshot": {
                "id": snapshot.id,
                "userId": snapshot.user_id,
                "parentSnapshotId": snapshot.parent_snapshot_id,
                "message": snapshot.message,
                "authorType": snapshot.author_type,
                "createdAt": snapshot.created_at.isoformat(),
            }
        }

    @router.post("/threads/create")
    async def create_thread(
        body: CreateThreadBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        thread = await service.create_thread(db, body.title)
        await db.commit()
        return {
            "thread": {
                "id": thread.id,
                "title": thread.title,
                "createdAt": thread.created_at.isoformat(),
                "updatedAt": thread.updated_at.isoformat(),
            }
        }

    @router.delete("/threads/{thread_id}")
    async def delete_thread(thread_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        try:
            await service.delete_thread(db, thread_id=thread_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="thread not found") from exc
        await db.commit()
        return {"deleted": True}

    @router.post("/chat/turn/stream")
    async def stream_chat_turn(
        body: ChatTurnBody,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> StreamingResponse:
        async def event_stream() -> Any:
            try:
                user_id = _resolve_user_id(request)
                await service.ensure_workspace_state(db)
                thread = await service.get_or_create_thread(db, body.threadId)
                rules = await service.list_rules(db)
                messages = await service.list_messages(db, thread.id)
                documents = await service.list_documents(db)
                skills = await skill_registry.list_skills(db)
                memory_candidates = await memory_service.list_memory_candidates(db, user_id=user_id)
                selected_memories = memory_service.rank_and_select_topk(
                    memories=memory_candidates,
                    user_message=body.message.strip(),
                )
                memory_summary = await memory_service.get_summary(db, user_id=user_id)
                skill_catalog = [
                    {
                        "id": skill.skill_id,
                        "name": skill.name,
                        "brief": skill.brief,
                        "enabled": skill.enabled,
                        "allowedTools": list(skill.tool_policy.allowed_tools),
                    }
                    for skill in skills
                ]
                skill_definitions = {
                    skill.skill_id: {
                        "id": skill.skill_id,
                        "name": skill.name,
                        "brief": skill.brief,
                        "enabled": skill.enabled,
                        "prompt": skill.prompt,
                        "toolPolicy": {
                            "allowedTools": list(skill.tool_policy.allowed_tools),
                            "requiredOrder": list(skill.tool_policy.required_order),
                            "blockedCombinations": [list(pair) for pair in skill.tool_policy.blocked_combinations],
                        },
                    }
                    for skill in skills
                }
                context = AgentTurnContext(
                    thread_id=thread.id,
                    user_id=user_id,
                    user_message=body.message.strip(),
                    recent_messages=[AgentMessage(role=item.role, content=item.content) for item in messages[-20:]],
                    active_rules=[rule.rule_text for rule in rules if rule.is_active],
                    document_keys=[doc.doc_key for doc in documents],
                    memory_facts=[
                        {
                            "key": memory.memory_key,
                            "value": memory.memory_value_text,
                            "confidence": round(float(memory.confidence), 2),
                            "type": memory.memory_type,
                        }
                        for memory in selected_memories
                    ],
                    memory_summary=memory_summary.summary_text if memory_summary else None,
                    skill_catalog=skill_catalog,
                    skill_definitions=skill_definitions,
                    loaded_skill_ids=[],
                    skill_request_limit=1,
                )
                yield to_sse("turn_started", {"threadId": thread.id})
                yield to_sse("memory_retrieved", {"count": len(selected_memories)})
                final_text = ""
                memory_suggestions: list[dict[str, Any]] | None = None
                async for event in runtime.run_turn_stream(context):
                    if event.get("type") == "token":
                        yield to_sse("token", {"text": event.get("text", "")})
                    elif event.get("type") == "tool_called":
                        yield to_sse("tool_called", {"toolName": event.get("toolName"), "metadata": event.get("metadata", {})})
                    elif event.get("type") == "skill_requested":
                        yield to_sse("skill_requested", {"metadata": event.get("metadata", {})})
                    elif event.get("type") == "skill_loaded":
                        yield to_sse("skill_loaded", {"metadata": event.get("metadata", {})})
                    elif event.get("type") == "skill_rejected":
                        yield to_sse("skill_rejected", {"metadata": event.get("metadata", {})})
                    elif event.get("type") == "turn_completed":
                        final_text = event.get("text", "") or ""
                        metadata = event.get("metadata", {})
                        if isinstance(metadata, dict):
                            suggestions = metadata.get("memorySuggestionCandidates")
                            if isinstance(suggestions, list):
                                memory_suggestions = [item for item in suggestions if isinstance(item, dict)]
                    elif event.get("type") == "turn_failed":
                        yield to_sse("turn_failed", {"error": event.get("error", "agent turn failed")})
                        return

                user_message, assistant_message = await service.append_turn_messages(
                    db,
                    thread=thread,
                    user_content=body.message,
                    assistant_content=final_text,
                )
                updated_documents = await service.list_documents(db)
                heads = await service.get_document_heads(db, doc_keys=[doc.doc_key for doc in updated_documents])
                await db.commit()
                await memory_jobs.enqueue_memory_job(
                    MemoryJob(
                        job_id=f"{thread.id}:{user_message.id}",
                        user_id=user_id,
                        thread_id=thread.id,
                        source_message_id=user_message.id,
                        user_message=body.message,
                        assistant_message=final_text,
                        suggested_candidates=memory_suggestions,
                    )
                )
                yield to_sse(
                    "turn_completed",
                    {
                        "threadId": thread.id,
                        "assistantMessage": {
                            "id": assistant_message.id,
                            "role": assistant_message.role,
                            "content": assistant_message.content,
                            "createdAt": assistant_message.created_at.isoformat(),
                        },
                        "documents": [service.serialize_document(doc=doc, head=heads.get(doc.doc_key)) for doc in updated_documents],
                    },
                )
            except Exception as exc:
                yield to_sse("turn_failed", {"error": str(exc)})

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @router.get("/skills")
    async def list_skills(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        skills = await skill_registry.list_catalog(db)
        await db.commit()
        return {
            "skills": [
                _serialize_skill_entry(
                    {
                        "id": item.skill_id,
                        "name": item.name,
                        "brief": item.brief,
                        "enabled": item.enabled,
                        "allowedTools": list(item.allowed_tools),
                    }
                )
                for item in skills
            ]
        }

    @router.get("/skills/{skill_id}")
    async def get_skill(skill_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        skill = await skill_registry.get_skill(db, skill_id=skill_id)
        if skill is None:
            raise HTTPException(status_code=404, detail="skill not found")
        await db.commit()
        return {
            "skill": {
                "id": skill.skill_id,
                "name": skill.name,
                "brief": skill.brief,
                "prompt": skill.prompt,
                "enabled": skill.enabled,
                "allowedTools": list(skill.tool_policy.allowed_tools),
                "requiredOrder": list(skill.tool_policy.required_order),
                "blockedCombinations": [list(pair) for pair in skill.tool_policy.blocked_combinations],
            }
        }

    @router.put("/skills/{skill_id}")
    async def update_skill(
        skill_id: str,
        body: UpdateSkillBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        row = await service.upsert_skill_override(
            db,
            skill_id=skill_id,
            enabled_override=body.enabled,
            name_override=body.name,
            brief_override=body.brief,
            prompt_override=body.prompt,
            allowed_tools_override=body.allowedTools,
            required_order_override=body.requiredOrder,
            blocked_combinations_override=body.blockedCombinations,
            is_active=True,
        )
        await db.commit()
        return {
            "skill": {
                "id": row.skill_id,
                "name": row.name_override or row.skill_id,
                "brief": row.brief_override or "",
                "prompt": row.prompt_override or "",
                "enabled": bool(row.enabled_override),
                "allowedTools": list(row.allowed_tools_override or []),
                "requiredOrder": list(row.required_order_override or []),
                "blockedCombinations": list(row.blocked_combinations_override or []),
            }
        }

    @router.delete("/skills/{skill_id}")
    async def delete_skill(skill_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        try:
            await service.delete_skill_override(db, skill_id=skill_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="skill not found") from exc
        await db.commit()
        return {"deleted": True}

    @router.get("/memories")
    async def list_memories(
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        rows = await memory_service.list_memory_candidates(db, user_id=user_id)
        summary = await memory_service.get_summary(db, user_id=user_id)
        await db.commit()
        return {
            "userId": user_id,
            "memories": [
                {
                    "id": row.id,
                    "key": row.memory_key,
                    "value": row.memory_value_text,
                    "type": row.memory_type,
                    "confidence": row.confidence,
                    "updatedAt": row.updated_at.isoformat(),
                }
                for row in rows
            ],
            "summary": summary.summary_text if summary else "",
            "summaryVersion": summary.source_version if summary else 0,
        }

    @router.get("/memories/{memory_id}")
    async def get_memory(
        memory_id: int,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        row = await memory_service.get_memory(db, user_id=user_id, memory_id=memory_id)
        if row is None:
            raise HTTPException(status_code=404, detail="memory not found")
        await db.commit()
        return {
            "memory": {
                "id": row.id,
                "key": row.memory_key,
                "value": row.memory_value_text,
                "type": row.memory_type,
                "confidence": row.confidence,
                "rationale": row.rationale,
                "updatedAt": row.updated_at.isoformat(),
            }
        }

    @router.put("/memories/{memory_id}")
    async def update_memory(
        memory_id: int,
        body: UpdateMemoryBody,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        try:
            row = await memory_service.update_memory(
                db,
                user_id=user_id,
                memory_id=memory_id,
                key=body.key,
                value_text=body.value,
                memory_type=body.type,
                confidence=body.confidence,
                rationale=body.rationale,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="memory not found") from exc
        await db.commit()
        return {
            "memory": {
                "id": row.id,
                "key": row.memory_key,
                "value": row.memory_value_text,
                "type": row.memory_type,
                "confidence": row.confidence,
                "rationale": row.rationale,
                "updatedAt": row.updated_at.isoformat(),
            }
        }

    @router.delete("/memories/{memory_id}")
    async def delete_memory(
        memory_id: int,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        try:
            await memory_service.delete_memory(db, user_id=user_id, memory_id=memory_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="memory not found") from exc
        await db.commit()
        return {"deleted": True}

    @router.put("/memories/summary")
    async def update_memory_summary(
        body: UpdateMemorySummaryBody,
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        summary = await memory_service.update_summary(db, user_id=user_id, summary_text=body.summary)
        await db.commit()
        return {
            "summary": summary.summary_text,
            "summaryVersion": summary.source_version,
            "updatedAt": summary.updated_at.isoformat(),
        }

    @router.delete("/memories/summary")
    async def delete_memory_summary(
        db: AsyncSession = Depends(get_db),
        request: Request = None,
    ) -> dict[str, Any]:
        user_id = _resolve_user_id(request)
        try:
            await memory_service.delete_summary(db, user_id=user_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="summary not found") from exc
        await db.commit()
        return {"deleted": True}

    @router.get("/notifications/stream")
    async def stream_notifications(request: Request) -> StreamingResponse:
        user_id = _resolve_user_id(request)

        async def event_stream() -> Any:
            queue = await broker.subscribe(user_id=user_id)
            try:
                yield to_sse("connected", {"userId": user_id})
                while True:
                    if await request.is_disconnected():
                        return
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=20.0)
                    except asyncio.TimeoutError:
                        yield to_sse("heartbeat", {"ts": "keepalive"})
                        continue
                    yield to_sse(str(event.get("event") or "message"), dict(event.get("payload") or {}))
            finally:
                await broker.unsubscribe(user_id=user_id, queue=queue)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @router.post("/rules")
    async def add_rule(
        body: AddRuleBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        rule = await service.add_rule(db, body.ruleText)
        await db.commit()
        return {
            "rule": {
                "id": rule.id,
                "ruleText": rule.rule_text,
                "isActive": rule.is_active,
                "createdAt": rule.created_at.isoformat(),
            }
        }

    @router.get("/rules")
    async def list_rules(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        rows = await service.list_rules(db)
        await db.commit()
        return {
            "rules": [
                {
                    "id": row.id,
                    "ruleText": row.rule_text,
                    "isActive": row.is_active,
                    "createdAt": row.created_at.isoformat(),
                    "updatedAt": row.updated_at.isoformat(),
                }
                for row in rows
            ]
        }

    @router.get("/rules/{rule_id}")
    async def get_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        row = await service.get_rule(db, rule_id=rule_id)
        if row is None:
            raise HTTPException(status_code=404, detail="rule not found")
        await db.commit()
        return {
            "rule": {
                "id": row.id,
                "ruleText": row.rule_text,
                "isActive": row.is_active,
                "createdAt": row.created_at.isoformat(),
                "updatedAt": row.updated_at.isoformat(),
            }
        }

    @router.put("/rules/{rule_id}")
    async def update_rule(
        rule_id: int,
        body: UpdateRuleBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        try:
            row = await service.update_rule(
                db,
                rule_id=rule_id,
                rule_text=body.ruleText,
                is_active=body.isActive,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="rule not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        await db.commit()
        return {
            "rule": {
                "id": row.id,
                "ruleText": row.rule_text,
                "isActive": row.is_active,
                "createdAt": row.created_at.isoformat(),
                "updatedAt": row.updated_at.isoformat(),
            }
        }

    @router.delete("/rules/{rule_id}")
    async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        try:
            await service.delete_rule(db, rule_id=rule_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="rule not found") from exc
        await db.commit()
        return {"deleted": True}

    @router.post("/documents/create")
    async def create_document(
        body: CreateDocumentBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        doc = await service.create_document(
            db,
            title=body.title,
            doc_key=body.docKey,
            initial_content=body.initialContent or "",
            author_type="user",
        )
        head = await service.ensure_document_head(db, doc=doc)
        await db.commit()
        return {"document": service.serialize_document(doc=doc, head=head)}

    @router.post("/documents/{doc_key}/working")
    async def update_document_working(
        doc_key: str,
        body: UpdateDocumentBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        try:
            doc = await service.update_working_document(
                db,
                doc_key=doc_key,
                content=body.content,
                author_type="user",
                message="Update working draft",
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        heads = await service.get_document_heads(db)
        await db.commit()
        head = heads.get(doc_key)
        return {
            "document": {
                "key": doc.doc_key,
                "title": doc.title,
                "content": doc.content,
                "currentRevisionId": head.current_revision_id if head else None,
            }
        }

    @router.post("/documents/checkpoint")
    async def checkpoint_documents(
        body: CheckpointBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        revisions = await service.checkpoint_workspace(
            db,
            message=(body.message or "Workspace checkpoint").strip(),
            author_type="user",
        )
        await db.commit()
        return {
            "revisions": {
                key: {
                    "id": rev.id,
                    "docKey": rev.doc_key,
                    "message": rev.message,
                    "createdAt": rev.created_at.isoformat(),
                }
                for key, rev in revisions.items()
            }
        }

    @router.post("/documents/{doc_key}/revisions")
    async def list_document_revisions(
        doc_key: str,
        body: RevisionListBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        revisions = await service.list_revisions(db, doc_key=doc_key, limit=body.limit)
        await db.commit()
        return {
            "revisions": [
                {
                    "id": item.id,
                    "docKey": item.doc_key,
                    "message": item.message,
                    "authorType": item.author_type,
                    "createdAt": item.created_at.isoformat(),
                }
                for item in revisions
            ]
        }

    @router.post("/documents/{doc_key}/revert")
    async def revert_document(
        doc_key: str,
        body: RevertBody,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        try:
            revision = await service.revert_document_to_revision(
                db,
                doc_key=doc_key,
                revision_id=body.revisionId,
                message=(body.message or "Revert document").strip(),
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="revision not found") from exc
        await db.commit()
        return {
            "revision": {
                "id": revision.id,
                "docKey": revision.doc_key,
                "message": revision.message,
                "createdAt": revision.created_at.isoformat(),
            }
        }

    @router.delete("/documents/{doc_key}")
    async def delete_document(doc_key: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        try:
            await service.delete_document(db, doc_key=doc_key)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="document not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        await db.commit()
        return {"deleted": True}

    return router

