from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReplyToolDescriptor:
    name: str = "reply"
    description: str = "Direct assistant response path (non-tool execution for v1)."
    enabled: bool = True

