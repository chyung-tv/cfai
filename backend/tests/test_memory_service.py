from __future__ import annotations

from datetime import UTC, datetime

from app.copilot.service.memory_service import MemoryService
from app.models.copilot.copilot_memory import CopilotMemory


def test_extract_candidates_from_turn_detects_preferences() -> None:
    service = MemoryService()
    candidates = service.extract_candidates_from_turn(
        user_message="I prefer concise answers and my risk tolerance is moderate.",
        assistant_message="Understood.",
    )
    keys = {item.key for item in candidates}
    assert "communication.preference" in keys or "communication.style" in keys
    assert "portfolio.risk_profile" in keys


def test_rank_and_select_topk_prioritizes_relevance() -> None:
    service = MemoryService()
    now = datetime.now(UTC)
    memory_a = CopilotMemory(
        user_id="u1",
        memory_key="communication.style",
        memory_value_text="concise",
        memory_type="preference",
        confidence=0.8,
        rationale="",
        is_active=True,
        updated_at=now,
    )
    memory_b = CopilotMemory(
        user_id="u1",
        memory_key="portfolio.risk_profile",
        memory_value_text="moderate",
        memory_type="risk_profile",
        confidence=0.7,
        rationale="",
        is_active=True,
        updated_at=now,
    )
    selected = service.rank_and_select_topk(memories=[memory_a, memory_b], user_message="Keep responses concise.")
    assert selected[0].memory_key == "communication.style"


def test_normalize_suggested_candidates_maps_alias_and_filters_skip() -> None:
    service = MemoryService()
    normalized = service.normalize_suggested_candidates(
        [
            {
                "key": "identity.name",
                "value": {"name": "yung"},
                "memoryType": "identity",
                "confidence": 0.99,
                "rationale": "explicit identity",
                "critical": True,
                "action": "upsert",
            },
            {
                "key": "communication.style",
                "value": {"style": "concise"},
                "memoryType": "preference",
                "confidence": 0.9,
                "action": "skip",
            },
        ]
    )
    assert len(normalized) == 1
    assert normalized[0].key == "profile.name"
    assert normalized[0].memory_type == "identity"
    assert normalized[0].critical is True


def test_normalize_suggested_candidates_coerces_scalar_values() -> None:
    service = MemoryService()
    normalized = service.normalize_suggested_candidates(
        [
            {
                "key": "communication.preference",
                "value": "please keep replies concise",
                "confidence": "0.7",
                "memoryType": "unknown_type",
                "action": "upsert",
            }
        ]
    )
    assert len(normalized) == 1
    assert normalized[0].value_text == "please keep replies concise"
    assert normalized[0].memory_type == "preference"
