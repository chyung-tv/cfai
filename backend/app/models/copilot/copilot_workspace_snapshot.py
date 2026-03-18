from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CopilotWorkspaceSnapshot(Base):
    __tablename__ = "copilot_workspace_snapshots"
    __table_args__ = (
        CheckConstraint(
            "author_type IN ('agent','user','system')",
            name="ck_copilot_workspace_snapshots_author_type",
        ),
        Index("ix_copilot_workspace_snapshots_user_created_at", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parent_snapshot_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("copilot_workspace_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    author_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="system")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
