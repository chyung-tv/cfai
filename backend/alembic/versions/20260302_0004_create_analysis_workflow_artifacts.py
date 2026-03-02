"""create analysis workflow artifacts table

Revision ID: 20260302_0004
Revises: 20260301_0003
Create Date: 2026-03-02 14:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260302_0004"
down_revision = "20260301_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_workflow_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "workflow_id",
            sa.String(length=36),
            sa.ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("artifact_type", sa.String(length=80), nullable=False),
        sa.Column("artifact_version", sa.String(length=40), nullable=False, server_default="v1"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_analysis_workflow_artifacts_workflow_id",
        "analysis_workflow_artifacts",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        "ix_analysis_workflow_artifacts_artifact_type",
        "analysis_workflow_artifacts",
        ["artifact_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analysis_workflow_artifacts_artifact_type",
        table_name="analysis_workflow_artifacts",
    )
    op.drop_index(
        "ix_analysis_workflow_artifacts_workflow_id",
        table_name="analysis_workflow_artifacts",
    )
    op.drop_table("analysis_workflow_artifacts")
