"""create workspace snapshot tables

Revision ID: 20260318_0012
Revises: 20260317_0011
Create Date: 2026-03-18 13:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260318_0012"
down_revision = "20260317_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "copilot_workspace_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("parent_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("message", sa.Text(), server_default="", nullable=False),
        sa.Column("author_type", sa.String(length=20), server_default="system", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "author_type IN ('agent','user','system')",
            name="ck_copilot_workspace_snapshots_author_type",
        ),
        sa.ForeignKeyConstraint(
            ["parent_snapshot_id"],
            ["copilot_workspace_snapshots.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_copilot_workspace_snapshots_user_id"),
        "copilot_workspace_snapshots",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_copilot_workspace_snapshots_user_created_at",
        "copilot_workspace_snapshots",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "copilot_workspace_snapshot_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_key", sa.String(length=160), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "entity_type IN ('document','rule','skill','memory','memory_summary')",
            name="ck_copilot_workspace_snapshot_items_entity_type",
        ),
        sa.ForeignKeyConstraint(["snapshot_id"], ["copilot_workspace_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "snapshot_id",
            "entity_type",
            "entity_key",
            name="uq_copilot_workspace_snapshot_items_snapshot_entity",
        ),
    )
    op.create_index(
        op.f("ix_copilot_workspace_snapshot_items_snapshot_id"),
        "copilot_workspace_snapshot_items",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        "ix_copilot_workspace_snapshot_items_snapshot_entity_type",
        "copilot_workspace_snapshot_items",
        ["snapshot_id", "entity_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_copilot_workspace_snapshot_items_snapshot_entity_type",
        table_name="copilot_workspace_snapshot_items",
    )
    op.drop_index(op.f("ix_copilot_workspace_snapshot_items_snapshot_id"), table_name="copilot_workspace_snapshot_items")
    op.drop_table("copilot_workspace_snapshot_items")

    op.drop_index("ix_copilot_workspace_snapshots_user_created_at", table_name="copilot_workspace_snapshots")
    op.drop_index(op.f("ix_copilot_workspace_snapshots_user_id"), table_name="copilot_workspace_snapshots")
    op.drop_table("copilot_workspace_snapshots")
