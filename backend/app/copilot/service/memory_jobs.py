from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.copilot.service.memory_service import MemoryService
from app.copilot.service.notification_broker import NotificationBroker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MemoryJob:
    job_id: str
    user_id: str
    thread_id: str
    source_message_id: int | None
    user_message: str
    assistant_message: str
    suggested_candidates: list[dict[str, Any]] | None = None
    retries: int = 0


class MemoryJobRunner:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        memory_service: MemoryService,
        broker: NotificationBroker,
    ) -> None:
        self._session_factory = session_factory
        self._memory_service = memory_service
        self._broker = broker
        self._queue: asyncio.Queue[MemoryJob] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._seen_job_ids: set[str] = set()

    async def start(self) -> None:
        if self._worker_task is not None and not self._worker_task.done():
            return
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        if self._worker_task is None:
            return
        self._worker_task.cancel()
        try:
            await self._worker_task
        except asyncio.CancelledError:
            pass
        self._worker_task = None

    async def enqueue_memory_job(self, job: MemoryJob) -> None:
        if job.job_id in self._seen_job_ids:
            return
        self._seen_job_ids.add(job.job_id)
        await self._queue.put(job)

    async def _worker_loop(self) -> None:
        while True:
            job = await self._queue.get()
            try:
                await self._process_job(job)
            except Exception as exc:  # pragma: no cover
                logger.exception("memory job failed", extra={"job_id": job.job_id, "user_id": job.user_id, "error": str(exc)})
                if job.retries < settings.memory_job_max_retries:
                    await self._queue.put(
                        MemoryJob(
                            job_id=job.job_id,
                            user_id=job.user_id,
                            thread_id=job.thread_id,
                            source_message_id=job.source_message_id,
                            user_message=job.user_message,
                            assistant_message=job.assistant_message,
                            suggested_candidates=job.suggested_candidates,
                            retries=job.retries + 1,
                        )
                    )
            finally:
                self._queue.task_done()

    async def _process_job(self, job: MemoryJob) -> None:
        async with self._session_factory() as db:
            used_suggestions = job.suggested_candidates is not None
            if used_suggestions:
                candidates = self._memory_service.normalize_suggested_candidates(job.suggested_candidates or [])
            else:
                candidates = []
            fallback_mode = (settings.memory_suggestion_fallback_mode or "rule_based").strip().lower()
            if not candidates and fallback_mode != "normalizer_only":
                candidates = self._memory_service.extract_candidates_from_turn(
                    user_message=job.user_message,
                    assistant_message=job.assistant_message,
                )
            if not candidates:
                logger.info(
                    "memory candidate extraction skipped",
                    extra={
                        "user_id": job.user_id,
                        "thread_id": job.thread_id,
                        "job_id": job.job_id,
                        "used_suggestions": used_suggestions,
                    },
                )
            written, critical_changed = await self._memory_service.upsert_memories(
                db,
                user_id=job.user_id,
                thread_id=job.thread_id,
                source_message_id=job.source_message_id,
                candidates=candidates,
            )
            summary = await self._memory_service.refresh_summary_if_needed(
                db,
                user_id=job.user_id,
                written_count=len(written),
                critical_key_changed=critical_changed,
            )
            await db.commit()

        if not candidates:
            reason = "llm_no_candidates" if job.suggested_candidates is not None else "no_candidates"
            await self._broker.publish(
                user_id=job.user_id,
                event="memory_rejected",
                payload={"reason": reason, "threadId": job.thread_id},
            )
            return
        if not written:
            logger.info(
                "memory write rejected",
                extra={"user_id": job.user_id, "thread_id": job.thread_id, "job_id": job.job_id, "reason": "low_confidence_or_duplicate"},
            )
            await self._broker.publish(
                user_id=job.user_id,
                event="memory_rejected",
                payload={"reason": "low_confidence_or_duplicate", "threadId": job.thread_id},
            )
            return

        logger.info(
            "memory write completed",
            extra={"user_id": job.user_id, "thread_id": job.thread_id, "job_id": job.job_id, "written_count": len(written)},
        )
        for item in written:
            await self._broker.publish(
                user_id=job.user_id,
                event="memory_written",
                payload={
                    "memoryKey": item.memory_key,
                    "memoryValue": item.memory_value_text,
                    "threadId": job.thread_id,
                },
            )
        if summary is not None:
            logger.info(
                "memory summary refreshed",
                extra={"user_id": job.user_id, "thread_id": job.thread_id, "job_id": job.job_id, "source_version": summary.source_version},
            )
            await self._broker.publish(
                user_id=job.user_id,
                event="summary_refreshed",
                payload={"sourceVersion": summary.source_version},
            )
