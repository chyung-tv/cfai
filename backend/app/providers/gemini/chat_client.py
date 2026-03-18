from __future__ import annotations

import asyncio
import queue
import threading
from collections.abc import AsyncGenerator
from typing import Any

from google import genai


class GeminiChatProviderError(Exception):
    pass


class GeminiChatClient:
    def __init__(
        self,
        *,
        vertex_api_key: str,
        vertex_project_id: str,
        vertex_location: str,
        use_vertex_ai: bool,
        model: str,
        enable_live_calls: bool,
    ) -> None:
        self._vertex_api_key = vertex_api_key
        self._vertex_project_id = vertex_project_id
        self._vertex_location = vertex_location
        self._use_vertex_ai = use_vertex_ai
        self._model = model
        self._enable_live_calls = enable_live_calls
        self._client: genai.Client | None = None

    async def stream_chat(self, *, prompt: str) -> AsyncGenerator[str, None]:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise GeminiChatProviderError("prompt is required")

        if not self._enable_live_calls:
            fallback = "Live chat model calls are disabled. Enable CHAT_ENABLE_LIVE_CALLS to use Gemini."
            for token in self._chunk_text(fallback):
                yield token
            return

        self._ensure_credentials()
        q: queue.Queue[tuple[str, str | None]] = queue.Queue()

        def worker() -> None:
            try:
                stream = self._get_client().models.generate_content_stream(
                    model=self._model,
                    contents=normalized_prompt,
                )
                for chunk in stream:
                    text = self._extract_chunk_text(chunk)
                    if text:
                        q.put(("token", text))
                q.put(("done", None))
            except Exception as exc:  # pragma: no cover - provider/network errors
                q.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

        while True:
            kind, payload = await asyncio.to_thread(q.get)
            if kind == "token" and payload is not None:
                yield payload
                continue
            if kind == "done":
                return
            if kind == "error":
                raise GeminiChatProviderError(payload or "gemini_stream_error")

    async def complete_chat(self, *, prompt: str) -> str:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise GeminiChatProviderError("prompt is required")
        if not self._enable_live_calls:
            return "Live chat model calls are disabled. Enable CHAT_ENABLE_LIVE_CALLS to use Gemini."
        self._ensure_credentials()
        try:
            return await asyncio.to_thread(self._generate_text, normalized_prompt)
        except Exception as exc:  # pragma: no cover - provider/network errors
            raise GeminiChatProviderError(str(exc)) from exc

    @staticmethod
    def _chunk_text(text: str) -> list[str]:
        return [f"{part} " for part in text.split()] or [text]

    @staticmethod
    def _extract_chunk_text(chunk: Any) -> str:
        direct = getattr(chunk, "text", None)
        if isinstance(direct, str):
            return direct
        candidates = getattr(chunk, "candidates", None)
        if isinstance(candidates, list):
            parts: list[str] = []
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                segment_parts = getattr(content, "parts", None)
                if isinstance(segment_parts, list):
                    for part in segment_parts:
                        text = getattr(part, "text", None)
                        if isinstance(text, str):
                            parts.append(text)
            return "".join(parts)
        return ""

    def _ensure_credentials(self) -> None:
        if self._use_vertex_ai:
            if self._vertex_api_key or self._vertex_project_id:
                return
            raise GeminiChatProviderError("missing Vertex credentials")
        if not self._vertex_api_key:
            raise GeminiChatProviderError("missing API key")

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if self._use_vertex_ai:
                if self._vertex_api_key:
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

    def _generate_text(self, prompt: str) -> str:
        response = self._get_client().models.generate_content(
            model=self._model,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
        candidates = getattr(response, "candidates", None)
        if isinstance(candidates, list):
            parts: list[str] = []
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                segment_parts = getattr(content, "parts", None)
                if isinstance(segment_parts, list):
                    for part in segment_parts:
                        part_text = getattr(part, "text", None)
                        if isinstance(part_text, str):
                            parts.append(part_text)
            merged = "".join(parts).strip()
            if merged:
                return merged
        return ""


__all__ = ["GeminiChatClient", "GeminiChatProviderError"]

