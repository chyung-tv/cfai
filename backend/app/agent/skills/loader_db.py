from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.skills.types import SkillSpec, ToolPolicy
from app.models.copilot.copilot_skill import CopilotSkill


class SkillDbLoader:
    async def ensure_seeded(self, db: AsyncSession, *, seeds: list[SkillSpec]) -> None:
        result = await db.execute(select(CopilotSkill))
        existing_by_id = {row.skill_id: row for row in result.scalars().all()}
        changed = False
        for seed in seeds:
            if seed.skill_id in existing_by_id:
                continue
            row = CopilotSkill(
                skill_id=seed.skill_id,
                enabled_override=seed.enabled,
                name_override=seed.name,
                brief_override=seed.brief,
                prompt_override=seed.prompt,
                allowed_tools_override=list(seed.tool_policy.allowed_tools),
                required_order_override=list(seed.tool_policy.required_order),
                blocked_combinations_override=[list(pair) for pair in seed.tool_policy.blocked_combinations],
                is_active=True,
            )
            db.add(row)
            changed = True
        if changed:
            await db.flush()

    async def list_skills(self, db: AsyncSession) -> list[SkillSpec]:
        result = await db.execute(select(CopilotSkill).where(CopilotSkill.is_active.is_(True)))
        rows = list(result.scalars().all())
        return sorted((_to_skill(row) for row in rows), key=lambda item: item.skill_id)


def _to_skill(row: CopilotSkill) -> SkillSpec:
    blocked: tuple[tuple[str, str], ...] = ()
    if isinstance(row.blocked_combinations_override, list):
        pairs: list[tuple[str, str]] = []
        for item in row.blocked_combinations_override:
            if (
                isinstance(item, list)
                and len(item) == 2
                and isinstance(item[0], str)
                and isinstance(item[1], str)
                and item[0].strip()
                and item[1].strip()
            ):
                pairs.append((item[0].strip(), item[1].strip()))
        blocked = tuple(pairs)

    allowed_tools: tuple[str, ...] = ()
    if isinstance(row.allowed_tools_override, list):
        allowed_tools = tuple(item.strip() for item in row.allowed_tools_override if isinstance(item, str) and item.strip())

    required_order: tuple[str, ...] = ()
    if isinstance(row.required_order_override, list):
        required_order = tuple(item.strip() for item in row.required_order_override if isinstance(item, str) and item.strip())

    return SkillSpec(
        skill_id=row.skill_id,
        name=row.name_override.strip() if isinstance(row.name_override, str) and row.name_override.strip() else row.skill_id,
        brief=row.brief_override.strip() if isinstance(row.brief_override, str) and row.brief_override.strip() else "",
        prompt=row.prompt_override.strip() if isinstance(row.prompt_override, str) and row.prompt_override.strip() else "",
        enabled=bool(row.enabled_override),
        tool_policy=ToolPolicy(
            allowed_tools=allowed_tools,
            required_order=required_order,
            blocked_combinations=blocked,
        ),
    )
