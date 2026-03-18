from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisWorkflow(Base):
    __tablename__ = "analysis_workflows"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued','running','completed','completed_cached','failed','cancelled')",
            name="ck_analysis_workflows_state",
        ),
        Index(
            "ix_analysis_workflows_symbol_state_updated_at",
            "symbol",
            "state",
            "updated_at",
        ),
        Index("ix_analysis_workflows_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )
    catalog_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("stock_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    substate: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    force_refresh: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
