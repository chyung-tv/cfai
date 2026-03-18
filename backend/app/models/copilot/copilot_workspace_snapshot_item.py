from __future__ import annotations

from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CopilotWorkspaceSnapshotItem(Base):
    __tablename__ = "copilot_workspace_snapshot_items"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('document','rule','skill','memory','memory_summary')",
            name="ck_copilot_workspace_snapshot_items_entity_type",
        ),
        UniqueConstraint(
            "snapshot_id",
            "entity_type",
            "entity_key",
            name="uq_copilot_workspace_snapshot_items_snapshot_entity",
        ),
        Index(
            "ix_copilot_workspace_snapshot_items_snapshot_entity_type",
            "snapshot_id",
            "entity_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("copilot_workspace_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_key: Mapped[str] = mapped_column(String(160), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
