"""create analysis workflow projections table

Revision ID: 20260304_0005
Revises: 20260302_0004
Create Date: 2026-03-04 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260304_0005"
down_revision = "20260302_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_workflow_projections",
        sa.Column(
            "workflow_id",
            sa.String(length=36),
            sa.ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("substate", sa.String(length=80), nullable=True),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.Column("latest_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contract_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("structured_output", sa.JSON(), nullable=True),
        sa.Column("reverse_dcf", sa.JSON(), nullable=True),
        sa.Column("audit_growth_likelihood", sa.JSON(), nullable=True),
        sa.Column("advisor_decision", sa.JSON(), nullable=True),
        sa.Column("normalization_warnings", sa.JSON(), nullable=True),
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
    op.create_index(
        "ix_analysis_workflow_projections_symbol",
        "analysis_workflow_projections",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        "ix_analysis_workflow_projections_state",
        "analysis_workflow_projections",
        ["state"],
        unique=False,
    )
    op.create_index(
        "ix_analysis_workflow_projections_symbol_updated_at",
        "analysis_workflow_projections",
        ["symbol", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analysis_workflow_projections_symbol_updated_at",
        table_name="analysis_workflow_projections",
    )
    op.drop_index(
        "ix_analysis_workflow_projections_state",
        table_name="analysis_workflow_projections",
    )
    op.drop_index(
        "ix_analysis_workflow_projections_symbol",
        table_name="analysis_workflow_projections",
    )
    op.drop_table("analysis_workflow_projections")
