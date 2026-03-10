from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisWorkflowEvent(Base):
    __tablename__ = "analysis_workflow_events"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued','running','completed','completed_cached','failed','cancelled')",
            name="ck_analysis_workflow_events_state",
        ),
        UniqueConstraint("workflow_id", "seq_no", name="uq_analysis_workflow_events_seq"),
        Index("ix_analysis_workflow_events_workflow_created_at", "workflow_id", "created_at"),
        Index("ix_analysis_workflow_events_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seq_no: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    substate: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, server_default="transition")
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
