from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchToolDescriptor:
    name: str = "run_research"
    description: str = "Deep research tool boundary."
    enabled: bool = False

