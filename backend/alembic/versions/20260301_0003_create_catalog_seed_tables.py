"""create catalog seed tables

Revision ID: 20260301_0003
Revises: 20260226_0002
Create Date: 2026-03-01 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260301_0003"
down_revision = "20260226_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_seed_runs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("endpoint_strategy", sa.String(length=30), nullable=False),
        sa.Column("request_params", sa.JSON(), nullable=True),
        sa.Column("endpoint_usage", sa.JSON(), nullable=True),
        sa.Column("expected_count", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("selected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("profile_coverage", sa.Float(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_catalog_seed_runs_status", "catalog_seed_runs", ["status"], unique=False)
    op.create_index(
        "ix_catalog_seed_runs_started_at",
        "catalog_seed_runs",
        ["started_at"],
        unique=False,
    )

    op.create_table(
        "stock_catalog",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("name_display", sa.String(length=255), nullable=False),
        sa.Column("name_normalized", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("exchange_short_name", sa.String(length=32), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("industry", sa.String(length=160), nullable=True),
        sa.Column("market_cap", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("selection_rank", sa.Integer(), nullable=True),
        sa.Column("selection_method", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="fmp"),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "seed_run_id",
            sa.String(length=36),
            sa.ForeignKey("catalog_seed_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("symbol", name="uq_stock_catalog_symbol"),
    )
    op.create_index("ix_stock_catalog_symbol", "stock_catalog", ["symbol"], unique=True)
    op.create_index(
        "ix_stock_catalog_name_normalized",
        "stock_catalog",
        ["name_normalized"],
        unique=False,
    )
    op.create_index("ix_stock_catalog_is_active", "stock_catalog", ["is_active"], unique=False)
    op.create_index(
        "ix_stock_catalog_selection_rank",
        "stock_catalog",
        ["selection_rank"],
        unique=False,
    )
    op.create_index("ix_stock_catalog_seed_run_id", "stock_catalog", ["seed_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stock_catalog_seed_run_id", table_name="stock_catalog")
    op.drop_index("ix_stock_catalog_selection_rank", table_name="stock_catalog")
    op.drop_index("ix_stock_catalog_is_active", table_name="stock_catalog")
    op.drop_index("ix_stock_catalog_name_normalized", table_name="stock_catalog")
    op.drop_index("ix_stock_catalog_symbol", table_name="stock_catalog")
    op.drop_table("stock_catalog")

    op.drop_index("ix_catalog_seed_runs_started_at", table_name="catalog_seed_runs")
    op.drop_index("ix_catalog_seed_runs_status", table_name="catalog_seed_runs")
    op.drop_table("catalog_seed_runs")
