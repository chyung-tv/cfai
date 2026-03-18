"""create copilot skills override table

Revision ID: 20260317_0010
Revises: 20260317_0009
Create Date: 2026-03-17 23:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260317_0010"
down_revision = "20260317_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "copilot_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.String(length=64), nullable=False),
        sa.Column("enabled_override", sa.Boolean(), nullable=True),
        sa.Column("name_override", sa.String(length=120), nullable=True),
        sa.Column("brief_override", sa.Text(), nullable=True),
        sa.Column("prompt_override", sa.Text(), nullable=True),
        sa.Column("allowed_tools_override", sa.JSON(), nullable=True),
        sa.Column("required_order_override", sa.JSON(), nullable=True),
        sa.Column("blocked_combinations_override", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", name="uq_copilot_skills_skill_id"),
    )
    op.create_index(op.f("ix_copilot_skills_skill_id"), "copilot_skills", ["skill_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_copilot_skills_skill_id"), table_name="copilot_skills")
    op.drop_table("copilot_skills")
