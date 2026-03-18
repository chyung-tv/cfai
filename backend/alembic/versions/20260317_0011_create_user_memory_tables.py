"""create user memory tables

Revision ID: 20260317_0011
Revises: 20260317_0010
Create Date: 2026-03-17 16:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260317_0011"
down_revision = "20260317_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "copilot_memories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("thread_id", sa.String(length=36), nullable=True),
        sa.Column("source_message_id", sa.Integer(), nullable=True),
        sa.Column("memory_key", sa.String(length=160), nullable=False),
        sa.Column("memory_value_json", sa.JSON(), nullable=False),
        sa.Column("memory_type", sa.String(length=40), server_default="preference", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("rationale", sa.Text(), server_default="", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_message_id"], ["copilot_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["thread_id"], ["copilot_threads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_copilot_memories_user_id"), "copilot_memories", ["user_id"], unique=False)
    op.create_index("ix_copilot_memories_user_active", "copilot_memories", ["user_id", "is_active"], unique=False)
    op.create_index(
        "ix_copilot_memories_user_key_active",
        "copilot_memories",
        ["user_id", "memory_key", "is_active"],
        unique=False,
    )
    op.create_index("ix_copilot_memories_user_updated", "copilot_memories", ["user_id", "updated_at"], unique=False)

    op.create_table(
        "copilot_memory_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("summary_text", sa.Text(), server_default="", nullable=False),
        sa.Column("source_version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_copilot_memory_summaries_user_id"),
    )
    op.create_index(op.f("ix_copilot_memory_summaries_user_id"), "copilot_memory_summaries", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_copilot_memory_summaries_user_id"), table_name="copilot_memory_summaries")
    op.drop_table("copilot_memory_summaries")
    op.drop_index("ix_copilot_memories_user_updated", table_name="copilot_memories")
    op.drop_index("ix_copilot_memories_user_key_active", table_name="copilot_memories")
    op.drop_index("ix_copilot_memories_user_active", table_name="copilot_memories")
    op.drop_index(op.f("ix_copilot_memories_user_id"), table_name="copilot_memories")
    op.drop_table("copilot_memories")
