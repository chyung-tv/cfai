"""create auth and workflow tables

Revision ID: 20260226_0002
Revises: 20260226_0001
Create Date: 2026-02-26 00:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260226_0002"
down_revision = "20260226_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("reset_token_hash", sa.String(length=128), nullable=True),
        sa.Column("reset_token_expires_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )
    op.create_index("ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"], unique=False)

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"], unique=False)
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)

    op.create_table(
        "analysis_workflows",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("substate", sa.String(length=80), nullable=True),
        sa.Column("force_refresh", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
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
    op.create_index("ix_analysis_workflows_user_id", "analysis_workflows", ["user_id"], unique=False)
    op.create_index("ix_analysis_workflows_symbol", "analysis_workflows", ["symbol"], unique=False)
    op.create_index("ix_analysis_workflows_state", "analysis_workflows", ["state"], unique=False)
    op.create_index("ix_analysis_workflows_substate", "analysis_workflows", ["substate"], unique=False)

    op.create_table(
        "analysis_workflow_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "workflow_id",
            sa.String(length=36),
            sa.ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("substate", sa.String(length=80), nullable=True),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_analysis_workflow_events_workflow_id",
        "analysis_workflow_events",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        "ix_analysis_workflow_events_state",
        "analysis_workflow_events",
        ["state"],
        unique=False,
    )
    op.create_index(
        "ix_analysis_workflow_events_substate",
        "analysis_workflow_events",
        ["substate"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_analysis_workflow_events_substate", table_name="analysis_workflow_events")
    op.drop_index("ix_analysis_workflow_events_state", table_name="analysis_workflow_events")
    op.drop_index("ix_analysis_workflow_events_workflow_id", table_name="analysis_workflow_events")
    op.drop_table("analysis_workflow_events")

    op.drop_index("ix_analysis_workflows_substate", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_state", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_symbol", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_user_id", table_name="analysis_workflows")
    op.drop_table("analysis_workflows")

    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index("ix_oauth_accounts_user_id", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
