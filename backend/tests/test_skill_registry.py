from __future__ import annotations

import asyncio

from app.agent.skills.registry import SkillRegistry
from app.agent.skills.types import SkillSpec, ToolPolicy


class _FakeDbLoader:
    async def ensure_seeded(self, db, *, seeds):  # noqa: ANN001
        self.seed_count = len(seeds)

    async def list_skills(self, db):  # noqa: ANN001
        return [
            SkillSpec(
                skill_id="documents_editing",
                name="Documents Editing",
                brief="Seeded from DB",
                prompt="Prompt",
                enabled=True,
                tool_policy=ToolPolicy(allowed_tools=("edit_document",)),
            )
        ]


def test_registry_reads_from_db_after_seed() -> None:
    loader = _FakeDbLoader()
    registry = SkillRegistry(db_loader=loader)
    skills = asyncio.run(registry.list_skills(db=None))  # type: ignore[arg-type]
    documents_skill = next(item for item in skills if item.skill_id == "documents_editing")
    assert loader.seed_count == 2
    assert documents_skill.brief == "Seeded from DB"
    assert documents_skill.tool_policy.allowed_tools == ("edit_document",)
