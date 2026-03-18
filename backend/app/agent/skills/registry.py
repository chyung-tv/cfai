from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.skills.loader_db import SkillDbLoader
from app.agent.skills.types import SkillCatalogEntry, SkillSpec, ToolPolicy

_DEFAULT_SEEDS: list[SkillSpec] = [
    SkillSpec(
        skill_id="documents_editing",
        name="Documents Editing",
        brief="Load when a turn needs to create or edit canonical documents.",
        prompt=(
            "Skill: Documents Editing\n"
            "- Use create_document only when a new canonical document is required.\n"
            "- Use edit_document for updates and prefer patch mode when possible.\n"
            "- Always preserve markdown validity and avoid deleting unrelated sections.\n"
            "- If required arguments are missing, ask a concise follow-up question instead of guessing."
        ),
        enabled=True,
        tool_policy=ToolPolicy(
            allowed_tools=("create_document", "edit_document"),
            required_order=(),
            blocked_combinations=(),
        ),
    ),
    SkillSpec(
        skill_id="research_deep",
        name="Deep Research",
        brief="Load when the user explicitly requests deep research synthesis.",
        prompt=(
            "Skill: Deep Research\n"
            "- Trigger this skill only for explicit deep-research requests.\n"
            "- Run run_research only when the user asks for deeper external synthesis.\n"
            "- Cite assumptions and limitations clearly in the final response."
        ),
        enabled=True,
        tool_policy=ToolPolicy(
            allowed_tools=("run_research",),
            required_order=(),
            blocked_combinations=(),
        ),
    ),
]


class SkillRegistry:
    def __init__(self, *, db_loader: SkillDbLoader | None = None) -> None:
        self._db_loader = db_loader or SkillDbLoader()

    async def list_catalog(self, db: AsyncSession) -> list[SkillCatalogEntry]:
        merged = await self.list_skills(db)
        return [
            SkillCatalogEntry(
                skill_id=skill.skill_id,
                name=skill.name,
                brief=skill.brief,
                enabled=skill.enabled,
                allowed_tools=skill.tool_policy.allowed_tools,
            )
            for skill in merged
        ]

    async def list_skills(self, db: AsyncSession) -> list[SkillSpec]:
        await self._db_loader.ensure_seeded(db, seeds=_DEFAULT_SEEDS)
        return await self._db_loader.list_skills(db)

    async def get_skill(self, db: AsyncSession, *, skill_id: str) -> SkillSpec | None:
        skills = await self.list_skills(db)
        requested = skill_id.strip()
        for skill in skills:
            if skill.skill_id == requested:
                return skill
        return None
