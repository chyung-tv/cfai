from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisSymbolSnapshot(Base):
    __tablename__ = "analysis_symbol_snapshots"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued','running','completed','completed_cached','failed','cancelled')",
            name="ck_analysis_symbol_snapshots_state",
        ),
        Index("ix_analysis_symbol_snapshots_updated_at", "updated_at"),
    )

    symbol: Mapped[str] = mapped_column(String(16), primary_key=True)
    catalog_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    latest_workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    freshness_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    contract_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

