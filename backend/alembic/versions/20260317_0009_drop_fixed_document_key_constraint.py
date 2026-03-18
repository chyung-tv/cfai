"""drop fixed canonical document key constraint

Revision ID: 20260317_0009
Revises: 20260317_0008
Create Date: 2026-03-17 21:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260317_0009"
down_revision = "20260317_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_copilot_canonical_documents_doc_key",
        "copilot_canonical_documents",
        type_="check",
    )


def downgrade() -> None:
    op.create_check_constraint(
        "ck_copilot_canonical_documents_doc_key",
        "copilot_canonical_documents",
        "doc_key IN ('portfolio_ledger','strategy_journal')",
    )
