from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class AgentTool(Protocol):
    name: str
    description: str
    enabled: bool

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    description: str
    enabled: bool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool

    def list_metadata(self) -> list[ToolMetadata]:
        return [
            ToolMetadata(name=tool.name, description=tool.description, enabled=tool.enabled)
            for tool in self._tools.values()
        ]

    def get(self, name: str) -> AgentTool | None:
        return self._tools.get(name)


@dataclass(frozen=True)
class DisabledPlaceholderTool:
    name: str
    description: str
    enabled: bool = False

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "disabled",
            "message": f"tool '{self.name}' is not enabled yet",
            "arguments": arguments,
        }

