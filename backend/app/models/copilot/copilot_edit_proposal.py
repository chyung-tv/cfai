from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CopilotEditProposal(Base):
    __tablename__ = "copilot_edit_proposals"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','applied','rejected')",
            name="ck_copilot_edit_proposals_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    thread_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("copilot_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    assistant_response: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_ledger_content: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    proposed_journal_content: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    proposed_ledger_patch: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    proposed_journal_patch: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    base_ledger_revision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("copilot_document_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    base_journal_revision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("copilot_document_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
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
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

