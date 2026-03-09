from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisWorkflowProjection(Base):
    __tablename__ = "analysis_workflow_projections"

    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
        primary_key=True,
    )
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    substate: Mapped[str | None] = mapped_column(String(80), nullable=True)
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latest_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    contract_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    result_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structured_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reverse_dcf: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    audit_growth_likelihood: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    advisor_decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    normalization_warnings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
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
