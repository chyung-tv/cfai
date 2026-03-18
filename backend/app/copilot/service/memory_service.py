from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
import re
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.copilot.copilot_memory import CopilotMemory
from app.models.copilot.copilot_memory_summary import CopilotMemorySummary

_RE_PREFERENCE = re.compile(r"\b(i prefer|i like|please use|i want)\b[:\s]*(.+)", re.IGNORECASE)
_RE_RISK = re.compile(r"\b(risk tolerance|risk profile)\b[:\s]*(.+)", re.IGNORECASE)
_RE_STYLE = re.compile(r"\b(be|keep it)\s+(concise|brief|detailed|technical)\b", re.IGNORECASE)
_RE_NAME = re.compile(r"\b(my name is|call me|remember my name is)\b[:\s]*(.+)", re.IGNORECASE)
_KEY_ALIASES = {
    "identity.name": "profile.name",
    "profile.full_name": "profile.name",
    "communication.tone": "communication.style",
}


@dataclass(frozen=True)
class MemoryCandidate:
    key: str
    value_text: str
    memory_type: str
    confidence: float
    rationale: str
    critical: bool = False


class MemoryService:
    async def list_memory_candidates(self, db: AsyncSession, *, user_id: str) -> list[CopilotMemory]:
        result = await db.execute(
            select(CopilotMemory)
            .where(
                and_(
                    CopilotMemory.user_id == user_id,
                    CopilotMemory.is_active.is_(True),
                )
            )
            .order_by(desc(CopilotMemory.updated_at))
            .limit(max(1, settings.memory_recall_max_candidates))
        )
        return list(result.scalars().all())

    def rank_and_select_topk(
        self,
        *,
        memories: list[CopilotMemory],
        user_message: str,
    ) -> list[CopilotMemory]:
        query = user_message.lower()
        now = datetime.now(UTC)
        scored: list[tuple[float, CopilotMemory]] = []
        for item in memories:
            score = float(item.confidence)
            age_hours = max(0.0, (now - item.updated_at).total_seconds() / 3600.0)
            recency_boost = max(0.0, 0.4 - min(0.4, age_hours / 200.0))
            score += recency_boost
            key = item.memory_key.lower()
            if key in query:
                score += 0.4
            value_blob = (item.memory_value_text or "").lower()
            if any(token in value_blob for token in query.split() if len(token) >= 4):
                score += 0.2
            if item.memory_type in {"constraint", "risk_profile"}:
                score += 0.2
            if "name" in query and item.memory_key in {"profile.name", "identity.name"}:
                score += 0.8
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        topk = max(1, settings.memory_prompt_topk)
        return [item for _, item in scored[:topk]]

    async def get_summary(self, db: AsyncSession, *, user_id: str) -> CopilotMemorySummary | None:
        result = await db.execute(
            select(CopilotMemorySummary).where(CopilotMemorySummary.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_memory(self, db: AsyncSession, *, user_id: str, memory_id: int) -> CopilotMemory | None:
        result = await db.execute(
            select(CopilotMemory).where(
                and_(
                    CopilotMemory.id == memory_id,
                    CopilotMemory.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_memory(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        memory_id: int,
        key: str,
        value_text: str,
        memory_type: str,
        confidence: float,
        rationale: str,
    ) -> CopilotMemory:
        row = await self.get_memory(db, user_id=user_id, memory_id=memory_id)
        if row is None:
            raise LookupError("memory_not_found")
        clean_key = key.strip().lower()
        if not clean_key:
            raise ValueError("memory_key_required")
        row.memory_key = _KEY_ALIASES.get(clean_key, clean_key)
        row.memory_value_text = value_text.strip()
        row.memory_type = memory_type.strip().lower() or "preference"
        row.confidence = max(0.0, min(1.0, float(confidence)))
        row.rationale = rationale.strip()
        row.updated_at = datetime.now(UTC)
        await db.flush()
        return row

    async def delete_memory(self, db: AsyncSession, *, user_id: str, memory_id: int) -> None:
        row = await self.get_memory(db, user_id=user_id, memory_id=memory_id)
        if row is None:
            raise LookupError("memory_not_found")
        await db.delete(row)
        await db.flush()

    async def update_summary(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        summary_text: str,
    ) -> CopilotMemorySummary:
        summary = await self.get_summary(db, user_id=user_id)
        if summary is None:
            summary = CopilotMemorySummary(
                user_id=user_id,
                summary_text=summary_text.strip(),
                source_version=1,
            )
            db.add(summary)
            await db.flush()
            return summary
        summary.summary_text = summary_text.strip()
        summary.source_version = max(0, int(summary.source_version)) + 1
        summary.updated_at = datetime.now(UTC)
        await db.flush()
        return summary

    async def delete_summary(self, db: AsyncSession, *, user_id: str) -> None:
        summary = await self.get_summary(db, user_id=user_id)
        if summary is None:
            raise LookupError("summary_not_found")
        await db.delete(summary)
        await db.flush()

    def extract_candidates_from_turn(
        self,
        *,
        user_message: str,
        assistant_message: str,
    ) -> list[MemoryCandidate]:
        text = user_message.strip()
        candidates: list[MemoryCandidate] = []

        preference_match = _RE_PREFERENCE.search(text)
        if preference_match:
            candidates.append(
                MemoryCandidate(
                    key="communication.preference",
                    value_text=preference_match.group(2).strip(),
                    memory_type="preference",
                    confidence=0.82,
                    rationale="Explicit preference phrase found in user message.",
                )
            )

        risk_match = _RE_RISK.search(text)
        if risk_match:
            candidates.append(
                MemoryCandidate(
                    key="portfolio.risk_profile",
                    value_text=risk_match.group(2).strip(),
                    memory_type="risk_profile",
                    confidence=0.9,
                    rationale="Explicit risk profile statement found.",
                    critical=True,
                )
            )

        style_match = _RE_STYLE.search(text)
        if style_match:
            candidates.append(
                MemoryCandidate(
                    key="communication.style",
                    value_text=style_match.group(2).strip().lower(),
                    memory_type="preference",
                    confidence=0.84,
                    rationale="Explicit response-style instruction found.",
                )
            )

        name_match = _RE_NAME.search(text)
        if name_match:
            raw_name = name_match.group(2).strip()
            normalized = re.split(r"[\.\,\!\?]", raw_name, maxsplit=1)[0].strip()
            if normalized:
                candidates.append(
                    MemoryCandidate(
                        key="profile.name",
                        value_text=normalized,
                        memory_type="identity",
                        confidence=0.96,
                        rationale="Explicit self-identity statement found in user message.",
                        critical=True,
                    )
                )

        # Avoid runaway writes from very short or uncertain turns.
        if len(text) < 8 or "?" in text[:12]:
            return []
        if assistant_message.strip().lower().startswith("i could not"):
            return []
        return candidates

    def normalize_suggested_candidates(self, raw_candidates: list[dict[str, Any]]) -> list[MemoryCandidate]:
        normalized: list[MemoryCandidate] = []
        if not raw_candidates:
            return normalized
        max_candidates = max(1, settings.memory_suggestion_max_candidates)
        for item in raw_candidates[:max_candidates]:
            if not isinstance(item, dict):
                continue
            action = str(item.get("action") or "upsert").strip().lower()
            if action == "skip":
                continue
            key = str(item.get("key") or "").strip().lower()
            if not key:
                continue
            key = _KEY_ALIASES.get(key, key)
            if not re.match(r"^[a-z0-9_.-]{3,80}$", key):
                continue
            raw_value = item.get("value")
            value_text: str
            if isinstance(raw_value, dict):
                if isinstance(raw_value.get("text"), str):
                    value_text = raw_value.get("text", "")
                else:
                    value_text = json.dumps(raw_value, ensure_ascii=True, sort_keys=True)
            elif raw_value is None:
                continue
            else:
                value_text = str(raw_value)
            value_text = value_text.strip()
            if not value_text:
                continue
            memory_type = str(item.get("memoryType") or item.get("memory_type") or "preference").strip().lower()
            if memory_type not in {"preference", "risk_profile", "identity", "constraint", "instruction"}:
                memory_type = "preference"
            confidence = item.get("confidence", 0.0)
            try:
                confidence_value = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence_value = 0.0
            rationale = str(item.get("rationale") or "model-suggested memory candidate").strip()
            critical = bool(item.get("critical", False))
            normalized.append(
                MemoryCandidate(
                    key=key,
                    value_text=value_text,
                    memory_type=memory_type,
                    confidence=confidence_value,
                    rationale=rationale,
                    critical=critical,
                )
            )
        return normalized

    async def upsert_memories(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        thread_id: str | None,
        source_message_id: int | None,
        candidates: list[MemoryCandidate],
    ) -> tuple[list[CopilotMemory], bool]:
        written: list[CopilotMemory] = []
        critical_changed = False
        for item in candidates:
            if item.confidence < settings.memory_write_confidence_threshold:
                continue
            existing_result = await db.execute(
                select(CopilotMemory).where(
                    CopilotMemory.user_id == user_id,
                    CopilotMemory.memory_key == item.key,
                    CopilotMemory.is_active.is_(True),
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing is None:
                row = CopilotMemory(
                    user_id=user_id,
                    thread_id=thread_id,
                    source_message_id=source_message_id,
                    memory_key=item.key,
                    memory_value_text=item.value_text,
                    memory_type=item.memory_type,
                    confidence=item.confidence,
                    rationale=item.rationale,
                    is_active=True,
                )
                db.add(row)
                written.append(row)
                if item.critical:
                    critical_changed = True
                continue
            if existing.memory_value_text == item.value_text:
                continue
            existing.memory_value_text = item.value_text
            existing.memory_type = item.memory_type
            existing.confidence = max(existing.confidence, item.confidence)
            existing.thread_id = thread_id
            existing.source_message_id = source_message_id
            existing.rationale = item.rationale
            existing.updated_at = datetime.now(UTC)
            written.append(existing)
            if item.critical:
                critical_changed = True
        await db.flush()
        return written, critical_changed

    async def refresh_summary_if_needed(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        written_count: int,
        critical_key_changed: bool,
    ) -> CopilotMemorySummary | None:
        all_memories = await self.list_memory_candidates(db, user_id=user_id)
        summary = await self.get_summary(db, user_id=user_id)
        now = datetime.now(UTC)
        summary_age_hours = 9999.0
        current_version = 0
        if summary is not None:
            summary_age_hours = max(0.0, (now - summary.updated_at).total_seconds() / 3600.0)
            current_version = summary.source_version

        injected_memory_chars = sum(
            len(item.memory_key) + len(item.memory_value_text or "") for item in all_memories[: settings.memory_prompt_topk]
        )
        accepted_since_last = max(0, written_count)
        should_trigger = any(
            (
                accepted_since_last >= settings.memory_compression_min_writes,
                injected_memory_chars > settings.memory_compression_injected_char_limit,
                critical_key_changed,
                summary_age_hours > settings.memory_compression_max_summary_age_hours and accepted_since_last > 0,
            )
        )
        if not should_trigger:
            return None
        if accepted_since_last == 0:
            return None
        if summary is not None and now - summary.updated_at < timedelta(minutes=settings.memory_compression_cooldown_minutes):
            return None

        compact_lines = [f"- {item.memory_key}: {item.memory_value_text}" for item in all_memories[: settings.memory_prompt_topk]]
        next_text = "User memory summary:\n" + "\n".join(compact_lines)
        next_text = next_text[: settings.memory_summary_max_chars]
        if summary is None:
            summary = CopilotMemorySummary(
                user_id=user_id,
                summary_text=next_text,
                source_version=current_version + 1,
            )
            db.add(summary)
        else:
            summary.summary_text = next_text
            summary.source_version = current_version + 1
            summary.updated_at = now
        await db.flush()
        return summary
