from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolPolicy:
    allowed_tools: tuple[str, ...] = ()
    required_order: tuple[str, ...] = ()
    blocked_combinations: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SkillSpec:
    skill_id: str
    name: str
    brief: str
    prompt: str
    enabled: bool
    tool_policy: ToolPolicy = field(default_factory=ToolPolicy)


@dataclass(frozen=True)
class SkillCatalogEntry:
    skill_id: str
    name: str
    brief: str
    enabled: bool
    allowed_tools: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillOverride:
    skill_id: str
    enabled: bool | None = None
    name: str | None = None
    brief: str | None = None
    prompt: str | None = None
    allowed_tools: tuple[str, ...] | None = None
    required_order: tuple[str, ...] | None = None
    blocked_combinations: tuple[tuple[str, str], ...] | None = None
