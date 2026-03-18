from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypedDict


@dataclass(frozen=True)
class AgentMessage:
    role: Literal["user", "assistant", "system"]
    content: str


@dataclass(frozen=True)
class AgentTurnContext:
    thread_id: str
    user_id: str
    user_message: str
    recent_messages: list[AgentMessage]
    active_rules: list[str]
    document_keys: list[str]
    memory_facts: list[dict[str, Any]]
    skill_catalog: list[dict[str, Any]]
    skill_definitions: dict[str, dict[str, Any]] | None = None
    loaded_skill_ids: list[str] | None = None
    skill_request_limit: int = 1
    memory_summary: str | None = None


class AgentEvent(TypedDict, total=False):
    type: Literal[
        "turn_started",
        "token",
        "tool_called",
        "skill_requested",
        "skill_loaded",
        "skill_rejected",
        "memory_retrieved",
        "turn_completed",
        "turn_failed",
    ]
    text: str
    error: str
    toolName: str
    metadata: dict[str, Any]

