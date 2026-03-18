from __future__ import annotations

from app.agent.runtime.engine import AgentRuntime


def test_extract_skill_requests_ignores_invalid_payloads() -> None:
    text = """
    <skill_request>{"id":"documents_editing","reason":"need docs updates"}</skill_request>
    <skill_request>{bad json}</skill_request>
    """
    _, requests = AgentRuntime._extract_skill_requests(text)
    assert len(requests) == 1
    assert requests[0]["id"] == "documents_editing"


def test_tool_policy_blocks_without_loaded_skill() -> None:
    allowed, reason = AgentRuntime._is_tool_allowed(
        name="edit_document",
        loaded_skills=[],
        executed_tools=[],
    )
    assert allowed is False
    assert "no skill loaded" in reason


def test_tool_policy_enforces_required_order() -> None:
    loaded_skills = [
        {
            "id": "documents_editing",
            "toolPolicy": {
                "allowedTools": ["create_document", "edit_document"],
                "requiredOrder": ["create_document", "edit_document"],
                "blockedCombinations": [],
            },
        }
    ]
    allowed, reason = AgentRuntime._is_tool_allowed(
        name="edit_document",
        loaded_skills=loaded_skills,
        executed_tools=[],
    )
    assert allowed is False
    assert "requires 'create_document' first" in reason


def test_parse_turn_envelope_accepts_valid_payload() -> None:
    raw = """
    {
      "assistant": {
        "text": "hello",
        "toolCalls": [{"name":"edit_document","arguments":{"doc_key":"ledger"}}]
      },
      "memorySuggestion": {
        "candidates": [
          {"key":"profile.name","value":{"name":"yung"},"memoryType":"identity","confidence":0.95,"rationale":"explicit","critical":true,"action":"upsert"}
        ]
      }
    }
    """
    payload, error = AgentRuntime._parse_turn_envelope(raw)
    assert error is None
    assert payload is not None
    assert payload["assistantText"] == "hello"
    assert len(payload["toolCalls"]) == 1
    assert len(payload["memorySuggestionCandidates"]) == 1


def test_parse_turn_envelope_rejects_invalid_tool_arguments() -> None:
    raw = """
    {
      "assistant": {
        "text": "hello",
        "toolCalls": [{"name":"edit_document","arguments":"bad"}]
      },
      "memorySuggestion": null
    }
    """
    payload, error = AgentRuntime._parse_turn_envelope(raw)
    assert payload is None
    assert error == "tool_call_arguments_invalid"
