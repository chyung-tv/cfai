from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class WorkflowState(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    completed_cached = "completed_cached"


@dataclass(frozen=True)
class Transition:
    workflow_id: str
    symbol: str
    state: WorkflowState
    substate: str | None
    message: str
    payload: dict[str, Any] | None = None
