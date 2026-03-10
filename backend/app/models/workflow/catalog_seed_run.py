from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, Index, Integer, JSON, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CatalogSeedRun(Base):
    __tablename__ = "catalog_seed_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','succeeded','failed','cancelled')",
            name="ck_catalog_seed_runs_status",
        ),
        CheckConstraint("expected_count >= 0", name="ck_catalog_seed_runs_expected_count_nonneg"),
        CheckConstraint("selected_count >= 0", name="ck_catalog_seed_runs_selected_count_nonneg"),
        CheckConstraint("inserted_count >= 0", name="ck_catalog_seed_runs_inserted_count_nonneg"),
        CheckConstraint("updated_count >= 0", name="ck_catalog_seed_runs_updated_count_nonneg"),
        CheckConstraint(
            "profile_coverage IS NULL OR (profile_coverage >= 0 AND profile_coverage <= 1)",
            name="ck_catalog_seed_runs_profile_coverage_range",
        ),
        Index(
            "uq_catalog_seed_runs_running_singleton",
            "status",
            unique=True,
            postgresql_where=text("status = 'running'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scope: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    endpoint_strategy: Mapped[str] = mapped_column(String(30), nullable=False)
    request_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    endpoint_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expected_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="500")
    selected_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    profile_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
