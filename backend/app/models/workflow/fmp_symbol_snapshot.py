from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FmpSymbolSnapshot(Base):
    __tablename__ = "fmp_symbol_snapshots"
    __table_args__ = (
        Index(
            "ix_fmp_symbol_snapshots_lookup",
            "symbol",
            "dataset_type",
            "period",
            "expires_at",
        ),
        Index("ix_fmp_symbol_snapshots_fetched_at", "fetched_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    catalog_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_catalog.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    dataset_type: Mapped[str] = mapped_column(String(40), nullable=False)
    period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

