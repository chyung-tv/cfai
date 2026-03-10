"""rearchitecture analysis and fmp cache

Revision ID: 20260310_0006
Revises: 20260304_0005
Create Date: 2026-03-10 15:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260310_0006"
down_revision = "20260304_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_analysis_workflow_projections_symbol_updated_at", table_name="analysis_workflow_projections")
    op.drop_index("ix_analysis_workflow_projections_state", table_name="analysis_workflow_projections")
    op.drop_index("ix_analysis_workflow_projections_symbol", table_name="analysis_workflow_projections")
    op.drop_table("analysis_workflow_projections")

    op.drop_index("ix_analysis_workflow_artifacts_artifact_type", table_name="analysis_workflow_artifacts")
    op.drop_index("ix_analysis_workflow_artifacts_workflow_id", table_name="analysis_workflow_artifacts")
    op.drop_table("analysis_workflow_artifacts")

    op.drop_index("ix_analysis_workflow_events_substate", table_name="analysis_workflow_events")
    op.drop_index("ix_analysis_workflow_events_state", table_name="analysis_workflow_events")
    op.drop_index("ix_analysis_workflow_events_workflow_id", table_name="analysis_workflow_events")
    op.drop_table("analysis_workflow_events")

    op.drop_index("ix_analysis_workflows_substate", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_state", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_symbol", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_user_id", table_name="analysis_workflows")
    op.drop_table("analysis_workflows")

    op.create_table(
        "analysis_workflows",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("catalog_id", sa.Integer(), sa.ForeignKey("stock_catalog.id", ondelete="SET NULL"), nullable=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("substate", sa.String(length=80), nullable=True),
        sa.Column("force_refresh", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
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
        sa.CheckConstraint(
            "state IN ('queued','running','completed','completed_cached','failed','cancelled')",
            name="ck_analysis_workflows_state",
        ),
    )
    op.create_index("ix_analysis_workflows_user_id", "analysis_workflows", ["user_id"], unique=False)
    op.create_index("ix_analysis_workflows_catalog_id", "analysis_workflows", ["catalog_id"], unique=False)
    op.create_index("ix_analysis_workflows_symbol", "analysis_workflows", ["symbol"], unique=False)
    op.create_index("ix_analysis_workflows_state", "analysis_workflows", ["state"], unique=False)
    op.create_index("ix_analysis_workflows_substate", "analysis_workflows", ["substate"], unique=False)
    op.create_index(
        "ix_analysis_workflows_symbol_state_updated_at",
        "analysis_workflows",
        ["symbol", "state", "updated_at"],
        unique=False,
    )
    op.create_index("ix_analysis_workflows_created_at", "analysis_workflows", ["created_at"], unique=False)

    op.execute(
        """
        CREATE OR REPLACE FUNCTION guard_analysis_workflow_transition() RETURNS trigger AS $$
        BEGIN
          IF OLD.state IN ('completed', 'completed_cached', 'failed', 'cancelled') AND NEW.state <> OLD.state THEN
            RAISE EXCEPTION 'invalid terminal state transition: % -> %', OLD.state, NEW.state;
          END IF;

          IF OLD.state = 'queued' AND NEW.state NOT IN ('queued', 'running', 'failed', 'cancelled') THEN
            RAISE EXCEPTION 'invalid queued transition: % -> %', OLD.state, NEW.state;
          END IF;

          IF OLD.state = 'running' AND NEW.state NOT IN ('running', 'completed', 'completed_cached', 'failed', 'cancelled') THEN
            RAISE EXCEPTION 'invalid running transition: % -> %', OLD.state, NEW.state;
          END IF;

          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_guard_analysis_workflow_transition
        BEFORE UPDATE OF state ON analysis_workflows
        FOR EACH ROW
        EXECUTE FUNCTION guard_analysis_workflow_transition();
        """
    )

    op.create_table(
        "analysis_workflow_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "workflow_id",
            sa.String(length=36),
            sa.ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seq_no", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("substate", sa.String(length=80), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False, server_default="transition"),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('queued','running','completed','completed_cached','failed','cancelled')",
            name="ck_analysis_workflow_events_state",
        ),
        sa.UniqueConstraint("workflow_id", "seq_no", name="uq_analysis_workflow_events_seq"),
    )
    op.create_index("ix_analysis_workflow_events_workflow_id", "analysis_workflow_events", ["workflow_id"], unique=False)
    op.create_index("ix_analysis_workflow_events_state", "analysis_workflow_events", ["state"], unique=False)
    op.create_index("ix_analysis_workflow_events_substate", "analysis_workflow_events", ["substate"], unique=False)
    op.create_index(
        "ix_analysis_workflow_events_workflow_created_at",
        "analysis_workflow_events",
        ["workflow_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_analysis_workflow_events_created_at", "analysis_workflow_events", ["created_at"], unique=False)

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
            "produced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "workflow_id",
            "artifact_type",
            "artifact_version",
            name="uq_analysis_workflow_artifact_versioned",
        ),
    )
    op.create_index("ix_analysis_workflow_artifacts_workflow_id", "analysis_workflow_artifacts", ["workflow_id"], unique=False)
    op.create_index("ix_analysis_workflow_artifacts_artifact_type", "analysis_workflow_artifacts", ["artifact_type"], unique=False)
    op.create_index(
        "ix_analysis_workflow_artifacts_workflow_type",
        "analysis_workflow_artifacts",
        ["workflow_id", "artifact_type"],
        unique=False,
    )

    op.create_table(
        "analysis_symbol_snapshots",
        sa.Column("symbol", sa.String(length=16), primary_key=True, nullable=False),
        sa.Column("catalog_id", sa.Integer(), sa.ForeignKey("stock_catalog.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "latest_workflow_id",
            sa.String(length=36),
            sa.ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("model_metadata", sa.JSON(), nullable=True),
        sa.Column("freshness_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contract_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('queued','running','completed','completed_cached','failed','cancelled')",
            name="ck_analysis_symbol_snapshots_state",
        ),
    )
    op.create_index("ix_analysis_symbol_snapshots_catalog_id", "analysis_symbol_snapshots", ["catalog_id"], unique=False)
    op.create_index("ix_analysis_symbol_snapshots_state", "analysis_symbol_snapshots", ["state"], unique=False)
    op.create_index("ix_analysis_symbol_snapshots_updated_at", "analysis_symbol_snapshots", ["updated_at"], unique=False)

    op.create_table(
        "analysis_candidate_cards",
        sa.Column("symbol", sa.String(length=16), primary_key=True, nullable=False),
        sa.Column("catalog_id", sa.Integer(), sa.ForeignKey("stock_catalog.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "latest_workflow_id",
            sa.String(length=36),
            sa.ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("valuation_signal", sa.String(length=40), nullable=True),
        sa.Column("recent_change_signal", sa.String(length=40), nullable=True),
        sa.Column("portfolio_impact_signal", sa.String(length=40), nullable=True),
        sa.Column("freshness_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("freshness_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("card_payload", sa.JSON(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_analysis_candidate_cards_catalog_id", "analysis_candidate_cards", ["catalog_id"], unique=False)
    op.create_index("ix_analysis_candidate_cards_quality_score", "analysis_candidate_cards", ["quality_score"], unique=False)
    op.create_index(
        "ix_analysis_candidate_cards_freshness_updated_at",
        "analysis_candidate_cards",
        ["freshness_updated_at"],
        unique=False,
    )
    op.create_index("ix_analysis_candidate_cards_updated_at", "analysis_candidate_cards", ["updated_at"], unique=False)

    op.create_table(
        "fmp_symbol_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("catalog_id", sa.Integer(), sa.ForeignKey("stock_catalog.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dataset_type", sa.String(length=40), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=True),
        sa.Column("endpoint", sa.String(length=120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fmp_symbol_snapshots_symbol", "fmp_symbol_snapshots", ["symbol"], unique=False)
    op.create_index("ix_fmp_symbol_snapshots_catalog_id", "fmp_symbol_snapshots", ["catalog_id"], unique=False)
    op.create_index(
        "ix_fmp_symbol_snapshots_lookup",
        "fmp_symbol_snapshots",
        ["symbol", "dataset_type", "period", "expires_at"],
        unique=False,
    )
    op.create_index("ix_fmp_symbol_snapshots_fetched_at", "fmp_symbol_snapshots", ["fetched_at"], unique=False)

    op.add_column("catalog_seed_runs", sa.Column("worker_id", sa.String(length=64), nullable=True))
    op.add_column("catalog_seed_runs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("catalog_seed_runs", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_check_constraint(
        "ck_catalog_seed_runs_status",
        "catalog_seed_runs",
        "status IN ('queued','running','succeeded','failed','cancelled')",
    )
    op.create_check_constraint(
        "ck_catalog_seed_runs_expected_count_nonneg",
        "catalog_seed_runs",
        "expected_count >= 0",
    )
    op.create_check_constraint(
        "ck_catalog_seed_runs_selected_count_nonneg",
        "catalog_seed_runs",
        "selected_count >= 0",
    )
    op.create_check_constraint(
        "ck_catalog_seed_runs_inserted_count_nonneg",
        "catalog_seed_runs",
        "inserted_count >= 0",
    )
    op.create_check_constraint(
        "ck_catalog_seed_runs_updated_count_nonneg",
        "catalog_seed_runs",
        "updated_count >= 0",
    )
    op.create_check_constraint(
        "ck_catalog_seed_runs_profile_coverage_range",
        "catalog_seed_runs",
        "profile_coverage IS NULL OR (profile_coverage >= 0 AND profile_coverage <= 1)",
    )
    op.create_index(
        "uq_catalog_seed_runs_running_singleton",
        "catalog_seed_runs",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'running'"),
    )

    op.create_check_constraint("ck_stock_catalog_symbol_upper", "stock_catalog", "symbol = UPPER(symbol)")
    op.create_check_constraint(
        "ck_stock_catalog_selection_rank_positive",
        "stock_catalog",
        "selection_rank IS NULL OR selection_rank > 0",
    )
    op.create_check_constraint(
        "ck_stock_catalog_market_cap_positive",
        "stock_catalog",
        "market_cap IS NULL OR market_cap > 0",
    )
    op.create_index("ix_users_reset_token_hash", "users", ["reset_token_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_reset_token_hash", table_name="users")
    op.drop_constraint("ck_stock_catalog_market_cap_positive", "stock_catalog", type_="check")
    op.drop_constraint("ck_stock_catalog_selection_rank_positive", "stock_catalog", type_="check")
    op.drop_constraint("ck_stock_catalog_symbol_upper", "stock_catalog", type_="check")

    op.drop_index("uq_catalog_seed_runs_running_singleton", table_name="catalog_seed_runs")
    op.drop_constraint("ck_catalog_seed_runs_profile_coverage_range", "catalog_seed_runs", type_="check")
    op.drop_constraint("ck_catalog_seed_runs_updated_count_nonneg", "catalog_seed_runs", type_="check")
    op.drop_constraint("ck_catalog_seed_runs_inserted_count_nonneg", "catalog_seed_runs", type_="check")
    op.drop_constraint("ck_catalog_seed_runs_selected_count_nonneg", "catalog_seed_runs", type_="check")
    op.drop_constraint("ck_catalog_seed_runs_expected_count_nonneg", "catalog_seed_runs", type_="check")
    op.drop_constraint("ck_catalog_seed_runs_status", "catalog_seed_runs", type_="check")
    op.drop_column("catalog_seed_runs", "attempt_count")
    op.drop_column("catalog_seed_runs", "heartbeat_at")
    op.drop_column("catalog_seed_runs", "worker_id")

    op.drop_index("ix_fmp_symbol_snapshots_fetched_at", table_name="fmp_symbol_snapshots")
    op.drop_index("ix_fmp_symbol_snapshots_lookup", table_name="fmp_symbol_snapshots")
    op.drop_index("ix_fmp_symbol_snapshots_catalog_id", table_name="fmp_symbol_snapshots")
    op.drop_index("ix_fmp_symbol_snapshots_symbol", table_name="fmp_symbol_snapshots")
    op.drop_table("fmp_symbol_snapshots")

    op.drop_index("ix_analysis_candidate_cards_updated_at", table_name="analysis_candidate_cards")
    op.drop_index("ix_analysis_candidate_cards_freshness_updated_at", table_name="analysis_candidate_cards")
    op.drop_index("ix_analysis_candidate_cards_quality_score", table_name="analysis_candidate_cards")
    op.drop_index("ix_analysis_candidate_cards_catalog_id", table_name="analysis_candidate_cards")
    op.drop_table("analysis_candidate_cards")

    op.drop_index("ix_analysis_symbol_snapshots_updated_at", table_name="analysis_symbol_snapshots")
    op.drop_index("ix_analysis_symbol_snapshots_state", table_name="analysis_symbol_snapshots")
    op.drop_index("ix_analysis_symbol_snapshots_catalog_id", table_name="analysis_symbol_snapshots")
    op.drop_table("analysis_symbol_snapshots")

    op.drop_index("ix_analysis_workflow_artifacts_workflow_type", table_name="analysis_workflow_artifacts")
    op.drop_index("ix_analysis_workflow_artifacts_artifact_type", table_name="analysis_workflow_artifacts")
    op.drop_index("ix_analysis_workflow_artifacts_workflow_id", table_name="analysis_workflow_artifacts")
    op.drop_table("analysis_workflow_artifacts")

    op.drop_index("ix_analysis_workflow_events_created_at", table_name="analysis_workflow_events")
    op.drop_index("ix_analysis_workflow_events_workflow_created_at", table_name="analysis_workflow_events")
    op.drop_index("ix_analysis_workflow_events_substate", table_name="analysis_workflow_events")
    op.drop_index("ix_analysis_workflow_events_state", table_name="analysis_workflow_events")
    op.drop_index("ix_analysis_workflow_events_workflow_id", table_name="analysis_workflow_events")
    op.drop_table("analysis_workflow_events")

    op.execute("DROP TRIGGER IF EXISTS trg_guard_analysis_workflow_transition ON analysis_workflows;")
    op.execute("DROP FUNCTION IF EXISTS guard_analysis_workflow_transition;")
    op.drop_index("ix_analysis_workflows_created_at", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_symbol_state_updated_at", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_substate", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_state", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_symbol", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_catalog_id", table_name="analysis_workflows")
    op.drop_index("ix_analysis_workflows_user_id", table_name="analysis_workflows")
    op.drop_table("analysis_workflows")
