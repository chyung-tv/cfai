from __future__ import annotations

from typing import Any

from app.providers.gemini_deep_research import GeminiDeepResearchClient


class AdvisorClient:
    """Thin wrapper around structured Gemini generation for advisor decisions."""

    def __init__(self, *, gemini_client: GeminiDeepResearchClient) -> None:
        self._gemini_client = gemini_client

    async def generate_advisor_decision(self, *, prompt: str) -> dict[str, Any]:
        return await self._gemini_client.generate_json_object(prompt=prompt)
