from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisCandidateCard(Base):
    __tablename__ = "analysis_candidate_cards"
    __table_args__ = (
        Index("ix_analysis_candidate_cards_quality_score", "quality_score"),
        Index("ix_analysis_candidate_cards_freshness_updated_at", "freshness_updated_at"),
        Index("ix_analysis_candidate_cards_updated_at", "updated_at"),
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
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuation_signal: Mapped[str | None] = mapped_column(String(40), nullable=True)
    recent_change_signal: Mapped[str | None] = mapped_column(String(40), nullable=True)
    portfolio_impact_signal: Mapped[str | None] = mapped_column(String(40), nullable=True)
    freshness_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    freshness_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    card_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

