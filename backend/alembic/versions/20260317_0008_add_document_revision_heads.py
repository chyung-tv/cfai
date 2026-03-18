"""add document revisions and heads

Revision ID: 20260317_0008
Revises: 20260317_0007
Create Date: 2026-03-17 16:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260317_0008"
down_revision = "20260317_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "copilot_document_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("doc_key", sa.String(length=64), nullable=False),
        sa.Column("parent_revision_id", sa.String(length=36), nullable=True),
        sa.Column("base_revision_id", sa.String(length=36), nullable=True),
        sa.Column("full_content", sa.Text(), nullable=False),
        sa.Column("patch_text", sa.Text(), server_default="", nullable=False),
        sa.Column("patch_format", sa.String(length=24), server_default="unified_diff", nullable=False),
        sa.Column("author_type", sa.String(length=20), server_default="system", nullable=False),
        sa.Column("message", sa.Text(), server_default="", nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "author_type IN ('agent','user','system')",
            name="ck_copilot_document_revisions_author_type",
        ),
        sa.ForeignKeyConstraint(["doc_key"], ["copilot_canonical_documents.doc_key"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["parent_revision_id"],
            ["copilot_document_revisions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["base_revision_id"],
            ["copilot_document_revisions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_copilot_document_revisions_doc_key"),
        "copilot_document_revisions",
        ["doc_key"],
        unique=False,
    )
    op.create_index(
        "ix_copilot_document_revisions_doc_created_at",
        "copilot_document_revisions",
        ["doc_key", "created_at"],
        unique=False,
    )

    op.create_table(
        "copilot_document_heads",
        sa.Column("doc_key", sa.String(length=64), nullable=False),
        sa.Column("current_revision_id", sa.String(length=36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["doc_key"], ["copilot_canonical_documents.doc_key"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["current_revision_id"],
            ["copilot_document_revisions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("doc_key"),
    )

    op.add_column(
        "copilot_edit_proposals",
        sa.Column("proposed_ledger_patch", sa.Text(), server_default="", nullable=False),
    )
    op.add_column(
        "copilot_edit_proposals",
        sa.Column("proposed_journal_patch", sa.Text(), server_default="", nullable=False),
    )
    op.add_column(
        "copilot_edit_proposals",
        sa.Column("base_ledger_revision_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "copilot_edit_proposals",
        sa.Column("base_journal_revision_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_copilot_edit_proposals_base_ledger_revision_id",
        "copilot_edit_proposals",
        "copilot_document_revisions",
        ["base_ledger_revision_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_copilot_edit_proposals_base_journal_revision_id",
        "copilot_edit_proposals",
        "copilot_document_revisions",
        ["base_journal_revision_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_copilot_edit_proposals_base_journal_revision_id", "copilot_edit_proposals", type_="foreignkey")
    op.drop_constraint("fk_copilot_edit_proposals_base_ledger_revision_id", "copilot_edit_proposals", type_="foreignkey")
    op.drop_column("copilot_edit_proposals", "base_journal_revision_id")
    op.drop_column("copilot_edit_proposals", "base_ledger_revision_id")
    op.drop_column("copilot_edit_proposals", "proposed_journal_patch")
    op.drop_column("copilot_edit_proposals", "proposed_ledger_patch")

    op.drop_table("copilot_document_heads")
    op.drop_index("ix_copilot_document_revisions_doc_created_at", table_name="copilot_document_revisions")
    op.drop_index(op.f("ix_copilot_document_revisions_doc_key"), table_name="copilot_document_revisions")
    op.drop_table("copilot_document_revisions")
