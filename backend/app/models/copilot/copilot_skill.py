from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CopilotSkill(Base):
    __tablename__ = "copilot_skills"
    __table_args__ = (UniqueConstraint("skill_id", name="uq_copilot_skills_skill_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    enabled_override: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    name_override: Mapped[str | None] = mapped_column(String(120), nullable=True)
    brief_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    allowed_tools_override: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    required_order_override: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    blocked_combinations_override: Mapped[list[list[str]] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @staticmethod
    def normalize_tool_lists(value: Any) -> list[str] | None:
        if not isinstance(value, list):
            return None
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
