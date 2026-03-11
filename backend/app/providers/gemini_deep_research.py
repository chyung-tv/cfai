from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass
from typing import Any

from google import genai


class DeepResearchProviderError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class DeepResearchCitation:
    title: str | None
    url: str | None
    publisher: str | None = None
    accessed_at: str | None = None


@dataclass(frozen=True)
class DeepResearchResult:
    interaction_id: str
    report_markdown: str
    citations: list[DeepResearchCitation]
    model_metadata: dict[str, Any]


@dataclass(frozen=True)
class StructuredOutputResult:
    structured_output: dict[str, Any]
    model_metadata: dict[str, Any]


class GeminiDeepResearchClient:
    def __init__(
        self,
        *,
        vertex_api_key: str,
        vertex_project_id: str,
        vertex_location: str,
        use_vertex_ai: bool,
        app_env: str,
        agent: str,
        deep_research_dev_model: str,
        deep_research_dev_grounding_enabled: bool,
        deep_research_use_endpoint_in_production: bool,
        structured_output_model: str,
        poll_interval_seconds: int,
        max_wait_seconds: int,
        enable_live_calls: bool,
    ) -> None:
        self._vertex_api_key = vertex_api_key
        self._vertex_project_id = vertex_project_id
        self._vertex_location = vertex_location
        self._use_vertex_ai = use_vertex_ai
        self._app_env = app_env
        self._agent = agent
        self._deep_research_dev_model = deep_research_dev_model
        self._deep_research_dev_grounding_enabled = deep_research_dev_grounding_enabled
        self._deep_research_use_endpoint_in_production = deep_research_use_endpoint_in_production
        self._structured_output_model = structured_output_model
        self._poll_interval_seconds = max(1, poll_interval_seconds)
        self._max_wait_seconds = max(10, max_wait_seconds)
        self._enable_live_calls = enable_live_calls
        self._client: genai.Client | None = None

    @property
    def structured_output_model_name(self) -> str:
        return self._structured_output_model

    async def run_report(self, *, prompt: str) -> DeepResearchResult:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise DeepResearchProviderError("invalid_prompt", "prompt is required")

        if not self._enable_live_calls:
            return DeepResearchResult(
                interaction_id="dry-run",
                report_markdown=(
                    "Deep research live call is disabled. "
                    "Enable DEEP_RESEARCH_ENABLE_LIVE_CALLS=true to execute."
                ),
                citations=[],
                model_metadata={
                    "mode": "dry_run",
                    "agent": self._agent,
                    "pollIntervalSeconds": self._poll_interval_seconds,
                    "maxWaitSeconds": self._max_wait_seconds,
                },
            )

        self._ensure_provider_credentials()

        if not self._use_deep_research_endpoint():
            response = await asyncio.to_thread(
                self._generate_content,
                self._deep_research_dev_model,
                normalized_prompt,
                self._deep_research_dev_grounding_enabled,
            )
            report_markdown = self._extract_response_text(response)
            if not report_markdown:
                raise DeepResearchProviderError("empty_report", "flash-lite path returned no text")
            return DeepResearchResult(
                interaction_id="flash-lite-dev",
                report_markdown=report_markdown,
                citations=[],
                model_metadata={
                    "mode": "flash_lite",
                    "model": self._deep_research_dev_model,
                    "groundingEnabled": self._deep_research_dev_grounding_enabled,
                    "status": "completed",
                },
            )

        interaction = await asyncio.to_thread(self._create_interaction, normalized_prompt)
        interaction_id = self._read_field(interaction, "id")
        if not interaction_id:
            raise DeepResearchProviderError("missing_interaction_id", "interaction id was missing")

        deadline = time.monotonic() + self._max_wait_seconds
        while time.monotonic() < deadline:
            current = await asyncio.to_thread(self._get_interaction, interaction_id)
            status = (self._read_field(current, "status") or "").lower()
            if status == "completed":
                report_markdown = self._extract_report_markdown(current)
                citations = self._extract_citations(current)
                if not report_markdown.strip():
                    raise DeepResearchProviderError("empty_report", "completed interaction returned no text")
                return DeepResearchResult(
                    interaction_id=interaction_id,
                    report_markdown=report_markdown,
                    citations=citations,
                    model_metadata={
                        "mode": "deep_research_endpoint",
                        "agent": self._agent,
                        "status": status,
                    },
                )
            if status == "failed":
                error_message = self._read_field(current, "error") or "deep research interaction failed"
                raise DeepResearchProviderError("provider_failed", str(error_message))

            await asyncio.sleep(self._poll_interval_seconds)

        raise DeepResearchProviderError(
            "provider_timeout",
            f"deep research exceeded max wait of {self._max_wait_seconds}s",
        )

    async def normalize_structured_output(self, *, prompt: str) -> StructuredOutputResult:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise DeepResearchProviderError("invalid_prompt", "structured output prompt is required")
        if not self._enable_live_calls:
            raise DeepResearchProviderError(
                "live_calls_disabled",
                "structured output normalization requires DEEP_RESEARCH_ENABLE_LIVE_CALLS=true",
            )
        self._ensure_provider_credentials()

        parsed = await self.generate_json_object(prompt=normalized_prompt)

        return StructuredOutputResult(
            structured_output=parsed,
            model_metadata={
                "model": self._structured_output_model,
                "status": "completed",
            },
        )

    async def generate_json_object(self, *, prompt: str) -> dict[str, Any]:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise DeepResearchProviderError("invalid_prompt", "json generation prompt is required")
        if not self._enable_live_calls:
            raise DeepResearchProviderError(
                "live_calls_disabled",
                "json generation requires DEEP_RESEARCH_ENABLE_LIVE_CALLS=true",
            )
        self._ensure_provider_credentials()

        response = await asyncio.to_thread(self._generate_structured_content, normalized_prompt)
        raw_text = self._extract_response_text(response)
        if not raw_text:
            raise DeepResearchProviderError("empty_structured_output", "model returned no text")

        parsed = self._parse_json_object(raw_text)
        if not isinstance(parsed, dict):
            raise DeepResearchProviderError("invalid_json_shape", "model output must be a JSON object")
        return parsed

    def _create_interaction(self, prompt: str) -> Any:
        return self._get_client().interactions.create(
            input=prompt,
            agent=self._agent,
            background=True,
            store=True,
        )

    def _generate_structured_content(self, prompt: str) -> Any:
        return self._generate_content(self._structured_output_model, prompt, False)

    def _generate_content(self, model: str, prompt: str, enable_grounding: bool) -> Any:
        config: dict[str, Any] | None = None
        if enable_grounding:
            # Dev/test grounding for flash-lite deep-research path.
            config = {"tools": [{"google_search": {}}]}
        return self._get_client().models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

    def _get_interaction(self, interaction_id: str) -> Any:
        return self._get_client().interactions.get(interaction_id)

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if self._use_vertex_ai:
                if self._vertex_api_key:
                    # Vertex Express Mode: API key auth does not accept project/location.
                    self._client = genai.Client(vertexai=True, api_key=self._vertex_api_key)
                else:
                    self._client = genai.Client(
                        vertexai=True,
                        project=self._vertex_project_id,
                        location=self._vertex_location,
                    )
            else:
                self._client = genai.Client(api_key=self._vertex_api_key)
        return self._client

    def _ensure_provider_credentials(self) -> None:
        if self._use_vertex_ai:
            if self._vertex_api_key:
                return
            if self._vertex_project_id:
                return
            raise DeepResearchProviderError(
                "missing_vertex_credentials",
                "Set VERTEX_AI_API_KEY (Express Mode) or VERTEX_AI_PROJECT_ID with ADC",
            )

        if not self._vertex_api_key:
            raise DeepResearchProviderError("missing_api_key", "VERTEX_AI_API_KEY is not configured")

    def _use_deep_research_endpoint(self) -> bool:
        if self._use_vertex_ai and self._vertex_api_key:
            # Vertex Express Mode uses API-key auth and currently runs via models.generate_content path.
            return False
        env = self._app_env.strip().lower()
        is_prod = env in {"production", "prod"}
        return is_prod and self._deep_research_use_endpoint_in_production

    @staticmethod
    def _read_field(obj: Any, field: str) -> Any:
        if obj is None:
            return None
        value = getattr(obj, field, None)
        if value is not None:
            return value
        if isinstance(obj, dict):
            return obj.get(field)
        return None

    def _extract_report_markdown(self, interaction: Any) -> str:
        outputs = self._read_field(interaction, "outputs")
        if not isinstance(outputs, list) or not outputs:
            return ""

        last_output = outputs[-1]
        direct_text = self._read_field(last_output, "text")
        if isinstance(direct_text, str):
            return direct_text

        content = self._read_field(last_output, "content")
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                text = self._read_field(item, "text")
                if isinstance(text, str):
                    parts.append(text)
            return "\n".join(parts).strip()
        return ""

    def _extract_citations(self, interaction: Any) -> list[DeepResearchCitation]:
        citation_rows = self._read_field(interaction, "citations")
        if not isinstance(citation_rows, list):
            return []

        parsed: list[DeepResearchCitation] = []
        for row in citation_rows:
            parsed.append(
                DeepResearchCitation(
                    title=self._read_field(row, "title"),
                    url=self._read_field(row, "url"),
                    publisher=self._read_field(row, "publisher"),
                    accessed_at=self._read_field(row, "accessedAt"),
                )
            )
        return parsed

    def _extract_response_text(self, response: Any) -> str:
        direct_text = self._read_field(response, "text")
        if isinstance(direct_text, str) and direct_text.strip():
            return direct_text.strip()

        candidates = self._read_field(response, "candidates")
        if isinstance(candidates, list):
            for candidate in candidates:
                content = self._read_field(candidate, "content")
                parts = self._read_field(content, "parts")
                if isinstance(parts, list):
                    chunks: list[str] = []
                    for part in parts:
                        text = self._read_field(part, "text")
                        if isinstance(text, str):
                            chunks.append(text)
                    if chunks:
                        return "\n".join(chunks).strip()
        return ""

    def _parse_json_object(self, raw_text: str) -> dict[str, Any]:
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", text)
            text = re.sub(r"\n```$", "", text)
            text = text.strip()

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError as exc:
                raise DeepResearchProviderError(
                    "invalid_json",
                    f"model returned invalid json: {exc}",
                ) from exc

        raise DeepResearchProviderError("invalid_json", "model returned non-json text")
