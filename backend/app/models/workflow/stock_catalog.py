from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StockCatalog(Base):
    __tablename__ = "stock_catalog"
    __table_args__ = (
        CheckConstraint("symbol = UPPER(symbol)", name="ck_stock_catalog_symbol_upper"),
        CheckConstraint(
            "selection_rank IS NULL OR selection_rank > 0",
            name="ck_stock_catalog_selection_rank_positive",
        ),
        CheckConstraint(
            "market_cap IS NULL OR market_cap > 0",
            name="ck_stock_catalog_market_cap_positive",
        ),
        Index("ix_stock_catalog_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    name_display: Mapped[str] = mapped_column(String(255), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exchange_short_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(160), nullable=True)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    selection_rank: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    selection_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, server_default="fmp")
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seed_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("catalog_seed_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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
