from __future__ import annotations

from collections.abc import AsyncGenerator
import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.agent.registry.tool_registry import ToolRegistry
from app.agent.runtime.turn_context import AgentEvent, AgentMessage, AgentTurnContext
from app.providers.gemini.chat_client import GeminiChatClient

_TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
_SKILL_REQUEST_RE = re.compile(r"<skill_request>\s*(\{.*?\})\s*</skill_request>", re.DOTALL)

logger = logging.getLogger(__name__)


class AgentRuntime:
    def __init__(self, *, chat_client: GeminiChatClient, tool_registry: ToolRegistry) -> None:
        self._chat_client = chat_client
        self._tool_registry = tool_registry

    async def run_turn_stream(self, context: AgentTurnContext) -> AsyncGenerator[AgentEvent, None]:
        skill_catalog = context.skill_catalog or []
        yield {
            "type": "turn_started",
            "metadata": {
                "threadId": context.thread_id,
                "availableTools": [
                    {"name": t.name, "description": t.description, "enabled": t.enabled}
                    for t in self._tool_registry.list_metadata()
                ],
                "availableSkills": skill_catalog,
                "memoryFactCount": len(context.memory_facts or []),
            },
        }

        try:
            pass1_prompt = self._build_prompt(context, phase="catalog", loaded_skills=[])
            pass1_text = await self._collect_response(pass1_prompt)
            _, requested_skills = self._extract_skill_requests(pass1_text)

            loaded_skills: list[dict[str, Any]] = []
            max_requests = max(0, context.skill_request_limit)
            for request in requested_skills[:max_requests]:
                requested_id = str(request.get("id") or "").strip()
                reason = str(request.get("reason") or "").strip()
                yield {"type": "skill_requested", "metadata": {"skillId": requested_id, "reason": reason}}
                skill = self._resolve_skill(context, requested_id)
                if skill is None:
                    yield {
                        "type": "skill_rejected",
                        "metadata": {
                            "skillId": requested_id,
                            "reason": "unknown_or_disabled_skill",
                        },
                    }
                    continue
                loaded_skills.append(skill)
                yield {
                    "type": "skill_loaded",
                    "metadata": {
                        "skillId": skill.get("id"),
                        "name": skill.get("name"),
                    },
                }

            prompt = self._build_prompt(context, phase="final", loaded_skills=loaded_skills)
            executed_tool_names: list[str] = []
            memory_suggestion_candidates: list[dict[str, Any]] | None = None
            if settings.turn_structured_output_enabled:
                structured = await self._collect_structured_response(prompt)
                clean_text = str(structured.get("assistantText") or "").strip()
                tool_calls = structured.get("toolCalls") if isinstance(structured.get("toolCalls"), list) else []
                if not tool_calls:
                    clean_text, tool_calls = self._extract_tool_calls(clean_text)
                suggestion_raw = structured.get("memorySuggestionCandidates")
                if isinstance(suggestion_raw, list):
                    memory_suggestion_candidates = suggestion_raw
            else:
                response_chunks: list[str] = []
                async for chunk in self._chat_client.stream_chat(prompt=prompt):
                    if not chunk:
                        continue
                    response_chunks.append(chunk)
                    yield {"type": "token", "text": chunk}
                final_text = "".join(response_chunks).strip()
                if not final_text:
                    final_text = "I could not generate a response for this turn."
                clean_text, tool_calls = self._extract_tool_calls(final_text)
            tool_notes: list[str] = []
            for call in tool_calls:
                name = call.get("name")
                arguments = call.get("arguments", {})
                if not isinstance(name, str) or not isinstance(arguments, dict):
                    continue
                allowed, reason = self._is_tool_allowed(name=name, loaded_skills=loaded_skills, executed_tools=executed_tool_names)
                if not allowed:
                    rejection = {
                        "status": "rejected",
                        "errorCode": "tool_not_allowed",
                        "message": reason,
                    }
                    yield {"type": "tool_called", "toolName": name, "metadata": rejection}
                    tool_notes.append(f"{name}: rejected ({reason})")
                    continue
                tool = self._tool_registry.get(name)
                if tool is None:
                    tool_notes.append(f"{name}: unavailable")
                    continue
                result = await tool.execute(arguments)
                yield {"type": "tool_called", "toolName": name, "metadata": result}
                status = str(result.get("status") or "ok")
                tool_notes.append(f"{name}: {status}")
                executed_tool_names.append(name)
            if tool_notes:
                suffix = "\n".join(f"- {note}" for note in tool_notes)
                clean_text = f"{clean_text}\n\nTool execution:\n{suffix}".strip()
            yield {
                "type": "turn_completed",
                "text": clean_text,
                "metadata": {"memorySuggestionCandidates": memory_suggestion_candidates or []},
            }
        except Exception as exc:
            logger.exception("agent turn failed", extra={"thread_id": context.thread_id})
            yield {"type": "turn_failed", "error": str(exc)}

    @staticmethod
    def _build_prompt(context: AgentTurnContext, *, phase: str, loaded_skills: list[dict[str, Any]]) -> str:
        lines: list[str] = [
            "You are CFAI Copilot in a portfolio co-editing workspace.",
            "Reply with concise, actionable text that helps the user decide next steps.",
            "Do not claim actions were executed unless explicitly confirmed.",
            "When a document operation is needed, emit tool calls in XML tags.",
            "<tool_call>{\"name\":\"create_document\",\"arguments\":{\"title\":\"...\",\"doc_key\":\"optional\",\"initial_content\":\"optional\"}}</tool_call>",
            "<tool_call>{\"name\":\"edit_document\",\"arguments\":{\"doc_key\":\"...\",\"mode\":\"replace|patch\",\"content\":\"...\",\"patch\":\"...\"}}</tool_call>",
            "Do not instruct users to change backend feature flags for normal chat replies.",
            "In regular chat, never ask for DEEP_RESEARCH_ENABLE_LIVE_CALLS.",
            "Treat deep research as disabled unless the user explicitly requests a deep research run.",
        ]
        if phase == "catalog":
            lines.extend(
                [
                    "Phase: skill selection.",
                    "Review available skills and request only those needed for this turn.",
                    "To request a skill, emit one or more tags in this format:",
                    "<skill_request>{\"id\":\"skill_id\",\"reason\":\"short reason\"}</skill_request>",
                    "Do not emit <tool_call> tags in this phase.",
                ]
            )
            if context.skill_catalog:
                lines.append("Available skills:")
                for skill in context.skill_catalog:
                    skill_id = str(skill.get("id") or "").strip()
                    name = str(skill.get("name") or "").strip()
                    brief = str(skill.get("brief") or "").strip()
                    enabled = bool(skill.get("enabled", False))
                    lines.append(f"- {skill_id} | {name} | enabled={enabled} | {brief}")
            else:
                lines.append("Available skills: none")
        else:
            lines.append("Phase: final response.")
            if loaded_skills:
                lines.append("Loaded skills:")
                for skill in loaded_skills:
                    lines.append(f"- {skill.get('id')}: {skill.get('name')}")
                    prompt = str(skill.get("prompt") or "").strip()
                    if prompt:
                        lines.append(prompt)
            else:
                lines.append("No additional skills were loaded for this turn.")
        if context.document_keys:
            lines.append("Available documents:")
            lines.extend(f"- {doc_key}" for doc_key in context.document_keys)
        if context.active_rules:
            lines.append("Active user rules:")
            lines.extend(f"- {rule}" for rule in context.active_rules)
        if context.memory_facts or context.memory_summary:
            lines.append("User memory context:")
            if context.memory_facts:
                lines.append("Top memory facts:")
                for item in context.memory_facts:
                    key = str(item.get("key") or "").strip()
                    value = item.get("value")
                    confidence = item.get("confidence")
                    if not key:
                        continue
                    lines.append(f"- {key} = {value} (confidence={confidence})")
            if context.memory_summary:
                lines.append("Memory summary:")
                lines.append(context.memory_summary.strip())
        if context.recent_messages:
            lines.append("Recent conversation:")
            for item in context.recent_messages[-12:]:
                role = item.role.upper()
                lines.append(f"{role}: {item.content}")
        lines.append(f"USER: {context.user_message}")
        lines.append("ASSISTANT:")
        return "\n".join(lines)

    @staticmethod
    def to_messages(*, user_message: str, assistant_message: str, history: list[AgentMessage]) -> list[AgentMessage]:
        base = history[-20:]
        return [*base, AgentMessage(role="user", content=user_message), AgentMessage(role="assistant", content=assistant_message)]

    @staticmethod
    def _extract_tool_calls(text: str) -> tuple[str, list[dict[str, Any]]]:
        calls: list[dict[str, Any]] = []
        for match in _TOOL_CALL_RE.finditer(text):
            raw = match.group(1).strip()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                calls.append(payload)
        clean_text = _TOOL_CALL_RE.sub("", text).strip()
        return clean_text, calls

    @staticmethod
    def _extract_skill_requests(text: str) -> tuple[str, list[dict[str, Any]]]:
        calls: list[dict[str, Any]] = []
        for match in _SKILL_REQUEST_RE.finditer(text):
            raw = match.group(1).strip()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                calls.append(payload)
        clean_text = _SKILL_REQUEST_RE.sub("", text).strip()
        return clean_text, calls

    async def _collect_response(self, prompt: str) -> str:
        chunks: list[str] = []
        async for chunk in self._chat_client.stream_chat(prompt=prompt):
            if chunk:
                chunks.append(chunk)
        return "".join(chunks).strip()

    async def _collect_structured_response(self, prompt: str) -> dict[str, Any]:
        max_attempts = max(1, settings.turn_schema_retry_max)
        current_prompt = self._build_structured_prompt(prompt)
        last_raw = ""
        last_error = "unknown"
        for attempt in range(max_attempts):
            raw = await self._chat_client.complete_chat(prompt=current_prompt)
            last_raw = raw
            parsed, error = self._parse_turn_envelope(raw)
            if parsed is not None:
                return parsed
            last_error = error or "invalid_schema"
            if not settings.turn_schema_repair_enabled or attempt >= max_attempts - 1:
                break
            current_prompt = self._build_repair_prompt(base_prompt=prompt, failed_output=raw, error=last_error)
        fallback_text = last_raw.strip() or "I could not generate a response for this turn."
        clean_fallback, extracted_calls = self._extract_tool_calls(fallback_text)
        return {
            "assistantText": clean_fallback or "I could not generate a response for this turn.",
            "toolCalls": extracted_calls,
            "memorySuggestionCandidates": [],
        }

    @staticmethod
    def _build_structured_prompt(base_prompt: str) -> str:
        return (
            f"{base_prompt}\n\n"
            "Return only valid JSON with this exact top-level schema:\n"
            "{\n"
            '  "assistant": {\n'
            '    "text": "string",\n'
            '    "toolCalls": [{"name":"string","arguments":{}}]\n'
            "  },\n"
            '  "memorySuggestion": {\n'
            '    "candidates": [\n'
            '      {"key":"string","value":{},"memoryType":"string","confidence":0.0,"rationale":"string","critical":false,"action":"upsert|skip"}\n'
            "    ]\n"
            "  }\n"
            "}\n"
            "Set memorySuggestion to null when no memory should be suggested.\n"
            "Do not output markdown, code fences, or extra commentary."
        )

    @staticmethod
    def _build_repair_prompt(*, base_prompt: str, failed_output: str, error: str) -> str:
        return (
            f"{base_prompt}\n\n"
            "Your previous output failed schema validation.\n"
            f"Error: {error}\n"
            "Rewrite the answer as strict JSON matching the required schema.\n"
            "No markdown fences. No prose outside JSON.\n"
            f"Previous output:\n{failed_output}"
        )

    @staticmethod
    def _parse_turn_envelope(raw: str) -> tuple[dict[str, Any] | None, str | None]:
        candidate = raw.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", candidate)
            candidate = re.sub(r"\s*```$", "", candidate)
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return None, "invalid_json"
        if not isinstance(payload, dict):
            return None, "root_not_object"
        assistant = payload.get("assistant")
        if not isinstance(assistant, dict):
            return None, "assistant_missing"
        text = assistant.get("text")
        if not isinstance(text, str):
            return None, "assistant_text_missing"
        tool_calls: list[dict[str, Any]] = []
        raw_calls = assistant.get("toolCalls")
        if raw_calls is not None:
            if not isinstance(raw_calls, list):
                return None, "tool_calls_not_list"
            for entry in raw_calls:
                if not isinstance(entry, dict):
                    return None, "tool_call_not_object"
                name = entry.get("name")
                arguments = entry.get("arguments", {})
                if not isinstance(name, str) or not name.strip():
                    return None, "tool_call_name_invalid"
                if not isinstance(arguments, dict):
                    return None, "tool_call_arguments_invalid"
                tool_calls.append({"name": name.strip(), "arguments": arguments})
        suggestion_candidates: list[dict[str, Any]] = []
        memory_suggestion = payload.get("memorySuggestion")
        if memory_suggestion is not None:
            if not isinstance(memory_suggestion, dict):
                return None, "memory_suggestion_not_object"
            raw_candidates = memory_suggestion.get("candidates", [])
            if not isinstance(raw_candidates, list):
                return None, "memory_candidates_not_list"
            for item in raw_candidates:
                if isinstance(item, dict):
                    suggestion_candidates.append(item)
        return {
            "assistantText": text.strip(),
            "toolCalls": tool_calls,
            "memorySuggestionCandidates": suggestion_candidates,
        }, None

    @staticmethod
    def _resolve_skill(context: AgentTurnContext, requested_id: str) -> dict[str, Any] | None:
        if not requested_id:
            return None
        definitions = context.skill_definitions or {}
        skill = definitions.get(requested_id)
        if not isinstance(skill, dict):
            return None
        if not bool(skill.get("enabled", False)):
            return None
        return skill

    @staticmethod
    def _is_tool_allowed(*, name: str, loaded_skills: list[dict[str, Any]], executed_tools: list[str]) -> tuple[bool, str]:
        if not loaded_skills:
            return False, "no skill loaded for tool execution"
        allowed_tools: set[str] = set()
        required_sequences: list[list[str]] = []
        blocked_pairs: list[tuple[str, str]] = []
        for skill in loaded_skills:
            policy = skill.get("toolPolicy")
            if not isinstance(policy, dict):
                continue
            allowed_raw = policy.get("allowedTools")
            if isinstance(allowed_raw, list):
                for item in allowed_raw:
                    if isinstance(item, str) and item.strip():
                        allowed_tools.add(item.strip())
            required_raw = policy.get("requiredOrder")
            if isinstance(required_raw, list):
                sequence = [item.strip() for item in required_raw if isinstance(item, str) and item.strip()]
                if sequence:
                    required_sequences.append(sequence)
            blocked_raw = policy.get("blockedCombinations")
            if isinstance(blocked_raw, list):
                for pair in blocked_raw:
                    if (
                        isinstance(pair, list)
                        and len(pair) == 2
                        and isinstance(pair[0], str)
                        and isinstance(pair[1], str)
                        and pair[0].strip()
                        and pair[1].strip()
                    ):
                        blocked_pairs.append((pair[0].strip(), pair[1].strip()))
        if name not in allowed_tools:
            return False, f"tool '{name}' not in loaded skill allowlist"
        for first, second in blocked_pairs:
            if name == first and second in executed_tools:
                return False, f"tool '{name}' blocked with '{second}' in same turn"
            if name == second and first in executed_tools:
                return False, f"tool '{name}' blocked with '{first}' in same turn"
        for sequence in required_sequences:
            if name not in sequence:
                continue
            idx = sequence.index(name)
            if idx <= 0:
                continue
            required_prev = sequence[idx - 1]
            if required_prev not in executed_tools:
                return False, f"tool '{name}' requires '{required_prev}' first"
        return True, "ok"

