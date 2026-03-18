from __future__ import annotations

from hashlib import sha256
from datetime import UTC, datetime
import re
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.copilot.canonical_document import CanonicalDocument
from app.models.copilot.copilot_document_head import CopilotDocumentHead
from app.models.copilot.copilot_document_revision import CopilotDocumentRevision
from app.models.copilot.copilot_memory import CopilotMemory
from app.models.copilot.copilot_memory_summary import CopilotMemorySummary
from app.models.copilot.copilot_message import CopilotMessage
from app.models.copilot.copilot_rule import CopilotRule
from app.models.copilot.copilot_skill import CopilotSkill
from app.models.copilot.copilot_thread import CopilotThread
from app.models.copilot.copilot_workspace_snapshot import CopilotWorkspaceSnapshot
from app.models.copilot.copilot_workspace_snapshot_item import CopilotWorkspaceSnapshotItem
from app.tools.documents.scripts.markdown_diff import unified_markdown_diff
from app.tools.documents.workflows.validate_patch import validate_document_content

LEDGER_KEY = "portfolio_ledger"
JOURNAL_KEY = "strategy_journal"

DEFAULT_LEDGER = """# Portfolio Ledger

| Symbol | Weight | Status | Notes |
| --- | ---: | --- | --- |
"""

DEFAULT_JOURNAL = """# Strategy Journal

## Initial Session
- Define target portfolio strategy.
- Use explicit approval before committing AI edits.
"""


def _content_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered or "document"


def _parse_optional_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class CopilotWorkspaceService:
    async def ensure_workspace_state(self, db: AsyncSession) -> tuple[CanonicalDocument, CanonicalDocument]:
        docs_result = await db.execute(
            select(CanonicalDocument).where(CanonicalDocument.doc_key.in_([LEDGER_KEY, JOURNAL_KEY]))
        )
        existing = {doc.doc_key: doc for doc in docs_result.scalars().all()}

        ledger = existing.get(LEDGER_KEY)
        if ledger is None:
            ledger = CanonicalDocument(
                doc_key=LEDGER_KEY,
                title="Portfolio Ledger",
                content=DEFAULT_LEDGER,
            )
            db.add(ledger)
        journal = existing.get(JOURNAL_KEY)
        if journal is None:
            journal = CanonicalDocument(
                doc_key=JOURNAL_KEY,
                title="Strategy Journal",
                content=DEFAULT_JOURNAL,
            )
            db.add(journal)
        await db.flush()
        await self.ensure_document_heads(db, ledger=ledger, journal=journal)
        return ledger, journal

    async def ensure_document_heads(
        self,
        db: AsyncSession,
        *,
        ledger: CanonicalDocument,
        journal: CanonicalDocument,
    ) -> tuple[CopilotDocumentHead, CopilotDocumentHead]:
        ledger_head = await self.ensure_document_head(db, doc=ledger)
        journal_head = await self.ensure_document_head(db, doc=journal)
        return ledger_head, journal_head

    async def get_document_heads(self, db: AsyncSession, *, doc_keys: list[str] | None = None) -> dict[str, CopilotDocumentHead]:
        query = select(CopilotDocumentHead)
        if doc_keys:
            query = query.where(CopilotDocumentHead.doc_key.in_(doc_keys))
        result = await db.execute(query)
        return {head.doc_key: head for head in result.scalars().all()}

    async def ensure_document_head(self, db: AsyncSession, *, doc: CanonicalDocument) -> CopilotDocumentHead:
        result = await db.execute(select(CopilotDocumentHead).where(CopilotDocumentHead.doc_key == doc.doc_key))
        head = result.scalar_one_or_none()
        if head is None:
            head = CopilotDocumentHead(doc_key=doc.doc_key)
            db.add(head)
            await db.flush()
        if not head.current_revision_id:
            revision = await self._append_revision(
                db,
                doc_key=doc.doc_key,
                content=doc.content,
                patch_text="",
                base_revision_id=None,
                parent_revision_id=None,
                author_type="system",
                message=f"Initial state: {doc.title}",
            )
            head.current_revision_id = revision.id
            await db.flush()
        return head

    async def _append_revision(
        self,
        db: AsyncSession,
        *,
        doc_key: str,
        content: str,
        patch_text: str,
        base_revision_id: str | None,
        parent_revision_id: str | None,
        author_type: str,
        message: str,
    ) -> CopilotDocumentRevision:
        revision = CopilotDocumentRevision(
            id=str(uuid4()),
            doc_key=doc_key,
            base_revision_id=base_revision_id,
            parent_revision_id=parent_revision_id,
            full_content=content,
            patch_text=patch_text,
            patch_format="unified_diff",
            author_type=author_type,
            message=message.strip(),
            content_hash=_content_hash(content),
        )
        db.add(revision)
        await db.flush()
        return revision

    async def get_or_create_thread(self, db: AsyncSession, thread_id: str | None) -> CopilotThread:
        if thread_id:
            existing = await db.execute(select(CopilotThread).where(CopilotThread.id == thread_id))
            thread = existing.scalar_one_or_none()
            if thread is not None:
                return thread

        latest = await db.execute(select(CopilotThread).order_by(desc(CopilotThread.updated_at)).limit(1))
        thread = latest.scalar_one_or_none()
        if thread is not None:
            return thread

        thread = CopilotThread(id=str(uuid4()), title="Primary Workspace")
        db.add(thread)
        await db.flush()
        return thread

    async def list_threads(self, db: AsyncSession) -> list[CopilotThread]:
        result = await db.execute(
            select(CopilotThread).order_by(desc(CopilotThread.updated_at), desc(CopilotThread.created_at)).limit(50)
        )
        return list(result.scalars().all())

    async def list_documents(self, db: AsyncSession) -> list[CanonicalDocument]:
        await self.ensure_workspace_state(db)
        result = await db.execute(select(CanonicalDocument).order_by(CanonicalDocument.updated_at.desc(), CanonicalDocument.doc_key.asc()))
        docs = list(result.scalars().all())
        for doc in docs:
            await self.ensure_document_head(db, doc=doc)
        return docs

    async def get_document(self, db: AsyncSession, *, doc_key: str) -> CanonicalDocument | None:
        result = await db.execute(select(CanonicalDocument).where(CanonicalDocument.doc_key == doc_key))
        doc = result.scalar_one_or_none()
        if doc is not None:
            await self.ensure_document_head(db, doc=doc)
        return doc

    async def create_document(
        self,
        db: AsyncSession,
        *,
        title: str,
        doc_key: str | None = None,
        initial_content: str = "",
        author_type: str = "user",
    ) -> CanonicalDocument:
        clean_title = (title or "").strip() or "Untitled Document"
        base_key = _slugify(doc_key or clean_title)
        candidate_key = base_key[:64]
        suffix = 2
        while await self.get_document(db, doc_key=candidate_key):
            suffix_str = f"_{suffix}"
            candidate_key = f"{base_key[: max(1, 64 - len(suffix_str))]}{suffix_str}"
            suffix += 1
        content = (initial_content or "").strip() or f"# {clean_title}\n"
        validate_document_content(doc_key=candidate_key, content=content)
        doc = CanonicalDocument(doc_key=candidate_key, title=clean_title[:120], content=content)
        db.add(doc)
        await db.flush()
        await self.ensure_document_head(db, doc=doc)
        return doc

    @staticmethod
    def serialize_document(*, doc: CanonicalDocument, head: CopilotDocumentHead | None) -> dict[str, str | None]:
        return {
            "key": doc.doc_key,
            "title": doc.title,
            "content": doc.content,
            "currentRevisionId": head.current_revision_id if head else None,
        }

    async def create_thread(self, db: AsyncSession, title: str | None = None) -> CopilotThread:
        clean_title = (title or "").strip() or "New Chat"
        thread = CopilotThread(id=str(uuid4()), title=clean_title[:160])
        db.add(thread)
        await db.flush()
        return thread

    async def list_messages(self, db: AsyncSession, thread_id: str) -> list[CopilotMessage]:
        result = await db.execute(
            select(CopilotMessage)
            .where(CopilotMessage.thread_id == thread_id)
            .order_by(CopilotMessage.created_at.asc(), CopilotMessage.id.asc())
            .limit(200)
        )
        return list(result.scalars().all())

    async def append_turn_messages(
        self,
        db: AsyncSession,
        *,
        thread: CopilotThread,
        user_content: str,
        assistant_content: str,
    ) -> tuple[CopilotMessage, CopilotMessage]:
        user_message = CopilotMessage(
            thread_id=thread.id,
            role="user",
            content=user_content.strip(),
        )
        assistant_message = CopilotMessage(
            thread_id=thread.id,
            role="assistant",
            content=assistant_content.strip(),
        )
        db.add(user_message)
        db.add(assistant_message)
        thread.updated_at = datetime.now(UTC)
        await db.flush()
        return user_message, assistant_message

    async def list_rules(self, db: AsyncSession) -> list[CopilotRule]:
        result = await db.execute(
            select(CopilotRule)
            .where(CopilotRule.is_active.is_(True))
            .order_by(CopilotRule.created_at.asc(), CopilotRule.id.asc())
        )
        return list(result.scalars().all())

    async def add_rule(self, db: AsyncSession, rule_text: str) -> CopilotRule:
        rule = CopilotRule(rule_text=rule_text.strip())
        db.add(rule)
        await db.flush()
        return rule

    async def get_rule(self, db: AsyncSession, *, rule_id: int) -> CopilotRule | None:
        result = await db.execute(select(CopilotRule).where(CopilotRule.id == rule_id))
        return result.scalar_one_or_none()

    async def update_rule(self, db: AsyncSession, *, rule_id: int, rule_text: str) -> CopilotRule:
        row = await self.get_rule(db, rule_id=rule_id)
        if row is None:
            raise LookupError("rule_not_found")
        clean = rule_text.strip()
        if not clean:
            raise ValueError("rule_text_required")
        row.rule_text = clean
        await db.flush()
        return row

    async def delete_rule(self, db: AsyncSession, *, rule_id: int) -> None:
        row = await self.get_rule(db, rule_id=rule_id)
        if row is None:
            raise LookupError("rule_not_found")
        await db.delete(row)
        await db.flush()

    async def list_skill_overrides(self, db: AsyncSession) -> list[CopilotSkill]:
        result = await db.execute(
            select(CopilotSkill)
            .where(CopilotSkill.is_active.is_(True))
            .order_by(CopilotSkill.skill_id.asc(), CopilotSkill.id.asc())
        )
        return list(result.scalars().all())

    async def get_skill_override(self, db: AsyncSession, *, skill_id: str) -> CopilotSkill | None:
        normalized = skill_id.strip()
        if not normalized:
            return None
        result = await db.execute(select(CopilotSkill).where(CopilotSkill.skill_id == normalized))
        return result.scalar_one_or_none()

    async def upsert_skill_override(
        self,
        db: AsyncSession,
        *,
        skill_id: str,
        enabled_override: bool | None = None,
        name_override: str | None = None,
        brief_override: str | None = None,
        prompt_override: str | None = None,
        allowed_tools_override: list[str] | None = None,
        required_order_override: list[str] | None = None,
        blocked_combinations_override: list[list[str]] | None = None,
        is_active: bool = True,
    ) -> CopilotSkill:
        normalized_id = skill_id.strip()
        if not normalized_id:
            raise ValueError("skill_id_required")
        existing_result = await db.execute(select(CopilotSkill).where(CopilotSkill.skill_id == normalized_id))
        row = existing_result.scalar_one_or_none()
        if row is None:
            row = CopilotSkill(skill_id=normalized_id)
            db.add(row)
            await db.flush()
        row.enabled_override = enabled_override
        row.name_override = name_override.strip() if isinstance(name_override, str) and name_override.strip() else None
        row.brief_override = brief_override.strip() if isinstance(brief_override, str) and brief_override.strip() else None
        row.prompt_override = prompt_override.strip() if isinstance(prompt_override, str) and prompt_override.strip() else None
        row.allowed_tools_override = CopilotSkill.normalize_tool_lists(allowed_tools_override)
        row.required_order_override = CopilotSkill.normalize_tool_lists(required_order_override)
        row.blocked_combinations_override = blocked_combinations_override
        row.is_active = is_active
        await db.flush()
        return row

    async def delete_skill_override(self, db: AsyncSession, *, skill_id: str) -> None:
        row = await self.get_skill_override(db, skill_id=skill_id)
        if row is None:
            raise LookupError("skill_not_found")
        await db.delete(row)
        await db.flush()

    async def update_working_document(
        self,
        db: AsyncSession,
        *,
        doc_key: str,
        content: str,
        author_type: str = "user",
        message: str = "Update working draft",
    ) -> CanonicalDocument:
        target = await self.get_document(db, doc_key=doc_key)
        if target is None:
            raise ValueError("invalid_doc_key")
        validate_document_content(doc_key=doc_key, content=content)
        previous_content = target.content
        target.content = content
        head = await self.ensure_document_head(db, doc=target)
        patch_text = unified_markdown_diff(
            before=previous_content,
            after=content,
            fromfile=f"a/{doc_key}.md",
            tofile=f"b/{doc_key}.md",
        )
        if previous_content != content:
            revision = await self._append_revision(
                db,
                doc_key=doc_key,
                content=content,
                patch_text=patch_text,
                base_revision_id=head.current_revision_id,
                parent_revision_id=head.current_revision_id,
                author_type=author_type,
                message=message,
            )
            head.current_revision_id = revision.id
        await db.flush()
        return target

    async def checkpoint_workspace(
        self,
        db: AsyncSession,
        *,
        message: str,
        author_type: str = "user",
    ) -> dict[str, CopilotDocumentRevision]:
        documents = await self.list_documents(db)
        heads = await self.get_document_heads(db, doc_keys=[doc.doc_key for doc in documents])

        revisions: dict[str, CopilotDocumentRevision] = {}
        for doc in documents:
            head = heads.get(doc.doc_key)
            if head is None:
                head = await self.ensure_document_head(db, doc=doc)
            revision = await self._append_revision(
                db,
                doc_key=doc.doc_key,
                content=doc.content,
                patch_text="",
                base_revision_id=head.current_revision_id,
                parent_revision_id=head.current_revision_id,
                author_type=author_type,
                message=message,
            )
            head.current_revision_id = revision.id
            revisions[doc.doc_key] = revision
        await db.flush()
        return revisions

    async def _latest_workspace_snapshot(
        self,
        db: AsyncSession,
        *,
        user_id: str,
    ) -> CopilotWorkspaceSnapshot | None:
        result = await db.execute(
            select(CopilotWorkspaceSnapshot)
            .where(CopilotWorkspaceSnapshot.user_id == user_id)
            .order_by(desc(CopilotWorkspaceSnapshot.created_at), desc(CopilotWorkspaceSnapshot.id))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_workspace_snapshot(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        message: str,
        author_type: str = "user",
    ) -> CopilotWorkspaceSnapshot:
        await self.ensure_workspace_state(db)
        documents = await self.list_documents(db)
        heads = await self.get_document_heads(db, doc_keys=[doc.doc_key for doc in documents])
        rules_result = await db.execute(select(CopilotRule).order_by(CopilotRule.created_at.asc(), CopilotRule.id.asc()))
        rules = list(rules_result.scalars().all())
        skills_result = await db.execute(select(CopilotSkill).order_by(CopilotSkill.skill_id.asc(), CopilotSkill.id.asc()))
        skills = list(skills_result.scalars().all())
        memories_result = await db.execute(
            select(CopilotMemory)
            .where(CopilotMemory.user_id == user_id)
            .order_by(CopilotMemory.updated_at.asc(), CopilotMemory.id.asc())
        )
        memories = list(memories_result.scalars().all())
        summary_result = await db.execute(
            select(CopilotMemorySummary).where(CopilotMemorySummary.user_id == user_id)
        )
        summary = summary_result.scalar_one_or_none()

        parent = await self._latest_workspace_snapshot(db, user_id=user_id)
        snapshot = CopilotWorkspaceSnapshot(
            id=str(uuid4()),
            user_id=user_id,
            parent_snapshot_id=parent.id if parent else None,
            message=message.strip(),
            author_type=author_type,
        )
        db.add(snapshot)
        await db.flush()

        snapshot_items: list[CopilotWorkspaceSnapshotItem] = []
        for doc in documents:
            snapshot_items.append(
                CopilotWorkspaceSnapshotItem(
                    snapshot_id=snapshot.id,
                    entity_type="document",
                    entity_key=doc.doc_key,
                    payload_json={
                        "docKey": doc.doc_key,
                        "title": doc.title,
                        "content": doc.content,
                        "currentRevisionId": heads.get(doc.doc_key).current_revision_id if heads.get(doc.doc_key) else None,
                    },
                )
            )
        for rule in rules:
            snapshot_items.append(
                CopilotWorkspaceSnapshotItem(
                    snapshot_id=snapshot.id,
                    entity_type="rule",
                    entity_key=str(rule.id),
                    payload_json={
                        "id": rule.id,
                        "ruleText": rule.rule_text,
                        "isActive": bool(rule.is_active),
                    },
                )
            )
        for skill in skills:
            snapshot_items.append(
                CopilotWorkspaceSnapshotItem(
                    snapshot_id=snapshot.id,
                    entity_type="skill",
                    entity_key=skill.skill_id,
                    payload_json={
                        "skillId": skill.skill_id,
                        "enabledOverride": skill.enabled_override,
                        "nameOverride": skill.name_override,
                        "briefOverride": skill.brief_override,
                        "promptOverride": skill.prompt_override,
                        "allowedToolsOverride": list(skill.allowed_tools_override or []),
                        "requiredOrderOverride": list(skill.required_order_override or []),
                        "blockedCombinationsOverride": list(skill.blocked_combinations_override or []),
                        "isActive": bool(skill.is_active),
                    },
                )
            )
        for memory in memories:
            snapshot_items.append(
                CopilotWorkspaceSnapshotItem(
                    snapshot_id=snapshot.id,
                    entity_type="memory",
                    entity_key=str(memory.id),
                    payload_json={
                        "memoryKey": memory.memory_key,
                        "memoryValueJson": memory.memory_value_json,
                        "memoryType": memory.memory_type,
                        "confidence": float(memory.confidence),
                        "rationale": memory.rationale,
                        "isActive": bool(memory.is_active),
                        "expiresAt": memory.expires_at.isoformat() if memory.expires_at else None,
                    },
                )
            )
        snapshot_items.append(
            CopilotWorkspaceSnapshotItem(
                snapshot_id=snapshot.id,
                entity_type="memory_summary",
                entity_key="summary",
                payload_json={
                    "summaryText": summary.summary_text if summary else "",
                    "sourceVersion": int(summary.source_version) if summary else 0,
                },
            )
        )

        db.add_all(snapshot_items)
        await db.flush()
        return snapshot

    async def list_workspace_snapshots(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        limit: int = 50,
    ) -> list[CopilotWorkspaceSnapshot]:
        result = await db.execute(
            select(CopilotWorkspaceSnapshot)
            .where(CopilotWorkspaceSnapshot.user_id == user_id)
            .order_by(desc(CopilotWorkspaceSnapshot.created_at), desc(CopilotWorkspaceSnapshot.id))
            .limit(max(1, min(limit, 200)))
        )
        return list(result.scalars().all())

    async def restore_workspace_snapshot(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        snapshot_id: str,
        message: str,
        author_type: str = "user",
    ) -> CopilotWorkspaceSnapshot:
        snapshot_result = await db.execute(
            select(CopilotWorkspaceSnapshot).where(
                CopilotWorkspaceSnapshot.id == snapshot_id,
                CopilotWorkspaceSnapshot.user_id == user_id,
            )
        )
        snapshot = snapshot_result.scalar_one_or_none()
        if snapshot is None:
            raise LookupError("snapshot_not_found")

        items_result = await db.execute(
            select(CopilotWorkspaceSnapshotItem)
            .where(CopilotWorkspaceSnapshotItem.snapshot_id == snapshot.id)
            .order_by(CopilotWorkspaceSnapshotItem.id.asc())
        )
        items = list(items_result.scalars().all())
        docs_payload = [item.payload_json for item in items if item.entity_type == "document"]
        rules_payload = [item.payload_json for item in items if item.entity_type == "rule"]
        skills_payload = [item.payload_json for item in items if item.entity_type == "skill"]
        memories_payload = [item.payload_json for item in items if item.entity_type == "memory"]
        summary_payload = next((item.payload_json for item in items if item.entity_type == "memory_summary"), {})

        existing_docs = await self.list_documents(db)
        existing_doc_keys = {doc.doc_key for doc in existing_docs}
        target_doc_keys = {
            str(payload.get("docKey"))
            for payload in docs_payload
            if isinstance(payload, dict) and isinstance(payload.get("docKey"), str)
        }
        for doc in existing_docs:
            if doc.doc_key not in target_doc_keys and doc.doc_key not in {LEDGER_KEY, JOURNAL_KEY}:
                await self.delete_document(db, doc_key=doc.doc_key)

        for payload in docs_payload:
            if not isinstance(payload, dict):
                continue
            doc_key = payload.get("docKey")
            content = payload.get("content")
            title = payload.get("title")
            if not isinstance(doc_key, str) or not isinstance(content, str):
                continue
            if doc_key in existing_doc_keys:
                target_doc = await self.get_document(db, doc_key=doc_key)
                if target_doc is None:
                    continue
                if isinstance(title, str) and title.strip():
                    target_doc.title = title.strip()[:120]
                await self.update_working_document(
                    db,
                    doc_key=doc_key,
                    content=content,
                    author_type=author_type,
                    message=message,
                )
            else:
                await self.create_document(
                    db,
                    title=title.strip()[:120] if isinstance(title, str) and title.strip() else doc_key,
                    doc_key=doc_key,
                    initial_content=content,
                    author_type=author_type,
                )

        existing_rules_result = await db.execute(select(CopilotRule))
        for row in existing_rules_result.scalars().all():
            await db.delete(row)
        for payload in rules_payload:
            if not isinstance(payload, dict):
                continue
            rule_text = payload.get("ruleText")
            if not isinstance(rule_text, str) or not rule_text.strip():
                continue
            db.add(CopilotRule(rule_text=rule_text.strip(), is_active=bool(payload.get("isActive", True))))

        existing_skills_result = await db.execute(select(CopilotSkill))
        for row in existing_skills_result.scalars().all():
            await db.delete(row)
        for payload in skills_payload:
            if not isinstance(payload, dict):
                continue
            skill_id = payload.get("skillId")
            if not isinstance(skill_id, str) or not skill_id.strip():
                continue
            db.add(
                CopilotSkill(
                    skill_id=skill_id.strip(),
                    enabled_override=payload.get("enabledOverride"),
                    name_override=payload.get("nameOverride"),
                    brief_override=payload.get("briefOverride"),
                    prompt_override=payload.get("promptOverride"),
                    allowed_tools_override=payload.get("allowedToolsOverride"),
                    required_order_override=payload.get("requiredOrderOverride"),
                    blocked_combinations_override=payload.get("blockedCombinationsOverride"),
                    is_active=bool(payload.get("isActive", True)),
                )
            )

        existing_memories_result = await db.execute(select(CopilotMemory).where(CopilotMemory.user_id == user_id))
        for row in existing_memories_result.scalars().all():
            await db.delete(row)
        for payload in memories_payload:
            if not isinstance(payload, dict):
                continue
            memory_key = payload.get("memoryKey")
            if not isinstance(memory_key, str) or not memory_key.strip():
                continue
            db.add(
                CopilotMemory(
                    user_id=user_id,
                    memory_key=memory_key.strip(),
                    memory_value_json=payload.get("memoryValueJson") if isinstance(payload.get("memoryValueJson"), dict) else {},
                    memory_type=str(payload.get("memoryType") or "preference"),
                    confidence=float(payload.get("confidence") or 0.0),
                    rationale=str(payload.get("rationale") or ""),
                    is_active=bool(payload.get("isActive", True)),
                    expires_at=_parse_optional_datetime(payload.get("expiresAt")),
                )
            )

        summary_result = await db.execute(
            select(CopilotMemorySummary).where(CopilotMemorySummary.user_id == user_id)
        )
        summary_row = summary_result.scalar_one_or_none()
        if summary_row is None:
            summary_row = CopilotMemorySummary(user_id=user_id)
            db.add(summary_row)
        summary_row.summary_text = str(summary_payload.get("summaryText") or "")
        summary_row.source_version = int(summary_payload.get("sourceVersion") or 0)
        await db.flush()

        restore_message = message.strip() or f"Restore snapshot {snapshot.id}"
        restored_snapshot = await self.create_workspace_snapshot(
            db,
            user_id=user_id,
            message=restore_message,
            author_type=author_type,
        )
        return restored_snapshot

    async def list_revisions(
        self,
        db: AsyncSession,
        *,
        doc_key: str,
        limit: int = 20,
    ) -> list[CopilotDocumentRevision]:
        result = await db.execute(
            select(CopilotDocumentRevision)
            .where(CopilotDocumentRevision.doc_key == doc_key)
            .order_by(desc(CopilotDocumentRevision.created_at))
            .limit(max(1, min(limit, 100)))
        )
        return list(result.scalars().all())

    async def revert_document_to_revision(
        self,
        db: AsyncSession,
        *,
        doc_key: str,
        revision_id: str,
        message: str,
    ) -> CopilotDocumentRevision:
        target_revision_result = await db.execute(
            select(CopilotDocumentRevision).where(
                CopilotDocumentRevision.id == revision_id,
                CopilotDocumentRevision.doc_key == doc_key,
            )
        )
        target_revision = target_revision_result.scalar_one_or_none()
        if target_revision is None:
            raise LookupError("revision_not_found")

        target_doc = await self.get_document(db, doc_key=doc_key)
        if target_doc is None:
            raise ValueError("invalid_doc_key")
        validate_document_content(doc_key=doc_key, content=target_revision.full_content)
        previous_content = target_doc.content
        target_doc.content = target_revision.full_content

        heads = await self.get_document_heads(db)
        head = heads[doc_key]
        patch_text = unified_markdown_diff(
            before=previous_content,
            after=target_doc.content,
            fromfile=f"a/{doc_key}.md",
            tofile=f"b/{doc_key}.md",
        )
        revert_revision = await self._append_revision(
            db,
            doc_key=doc_key,
            content=target_doc.content,
            patch_text=patch_text,
            base_revision_id=target_revision.id,
            parent_revision_id=head.current_revision_id,
            author_type="user",
            message=message,
        )
        head.current_revision_id = revert_revision.id
        await db.flush()
        return revert_revision

    async def delete_document(self, db: AsyncSession, *, doc_key: str) -> None:
        if doc_key in {LEDGER_KEY, JOURNAL_KEY}:
            raise ValueError("protected_document")
        doc = await self.get_document(db, doc_key=doc_key)
        if doc is None:
            raise LookupError("document_not_found")
        await db.delete(doc)
        await db.flush()


