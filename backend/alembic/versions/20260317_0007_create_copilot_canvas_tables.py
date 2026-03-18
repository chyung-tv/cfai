"""create copilot canvas tables

Revision ID: 20260317_0007
Revises: 49130e0f5e18
Create Date: 2026-03-17 11:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260317_0007"
down_revision = "49130e0f5e18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "copilot_canonical_documents",
        sa.Column("doc_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "doc_key IN ('portfolio_ledger','strategy_journal')",
            name="ck_copilot_canonical_documents_doc_key",
        ),
        sa.PrimaryKeyConstraint("doc_key"),
    )
    op.create_table(
        "copilot_threads",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=160), server_default="Workspace Thread", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "copilot_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('user','assistant','system')", name="ck_copilot_messages_role"),
        sa.ForeignKeyConstraint(["thread_id"], ["copilot_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_copilot_messages_thread_id"), "copilot_messages", ["thread_id"], unique=False)
    op.create_index(
        "ix_copilot_messages_thread_created_at",
        "copilot_messages",
        ["thread_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "copilot_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "copilot_edit_proposals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("thread_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("user_prompt", sa.Text(), nullable=False),
        sa.Column("assistant_response", sa.Text(), nullable=False),
        sa.Column("proposed_ledger_content", sa.Text(), server_default="", nullable=False),
        sa.Column("proposed_journal_content", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending','applied','rejected')",
            name="ck_copilot_edit_proposals_status",
        ),
        sa.ForeignKeyConstraint(["thread_id"], ["copilot_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_copilot_edit_proposals_thread_id"),
        "copilot_edit_proposals",
        ["thread_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_copilot_edit_proposals_thread_id"), table_name="copilot_edit_proposals")
    op.drop_table("copilot_edit_proposals")
    op.drop_table("copilot_rules")
    op.drop_index("ix_copilot_messages_thread_created_at", table_name="copilot_messages")
    op.drop_index(op.f("ix_copilot_messages_thread_id"), table_name="copilot_messages")
    op.drop_table("copilot_messages")
    op.drop_table("copilot_threads")
    op.drop_table("copilot_canonical_documents")

