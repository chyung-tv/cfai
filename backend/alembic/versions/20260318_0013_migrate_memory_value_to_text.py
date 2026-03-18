"""migrate memory value json to text

Revision ID: 20260318_0013
Revises: 20260318_0012
Create Date: 2026-03-18 18:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260318_0013"
down_revision = "20260318_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("copilot_memories", sa.Column("memory_value_text", sa.Text(), nullable=True, server_default=""))
    op.execute(
        """
        UPDATE copilot_memories
        SET memory_value_text = CASE
            WHEN jsonb_typeof(memory_value_json::jsonb) = 'object' AND (memory_value_json::jsonb ? 'text')
                THEN COALESCE(memory_value_json::jsonb ->> 'text', '')
            ELSE COALESCE(memory_value_json::text, '')
        END
        """
    )
    op.alter_column("copilot_memories", "memory_value_text", nullable=False)
    op.drop_column("copilot_memories", "memory_value_json")
    op.execute(
        """
        UPDATE copilot_workspace_snapshot_items
        SET payload_json = jsonb_set(
            (payload_json::jsonb - 'memoryValueJson'),
            '{memoryValueText}',
            to_jsonb(
                CASE
                    WHEN jsonb_typeof(payload_json::jsonb -> 'memoryValueJson') = 'object'
                        AND ((payload_json::jsonb -> 'memoryValueJson') ? 'text')
                    THEN COALESCE(payload_json::jsonb -> 'memoryValueJson' ->> 'text', '')
                    WHEN (payload_json::jsonb ? 'memoryValueText')
                    THEN COALESCE(payload_json::jsonb ->> 'memoryValueText', '')
                    ELSE COALESCE((payload_json::jsonb -> 'memoryValueJson')::text, '')
                END
            ),
            true
        )
        WHERE entity_type = 'memory'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE copilot_workspace_snapshot_items
        SET payload_json = jsonb_set(
            (payload_json::jsonb - 'memoryValueText'),
            '{memoryValueJson}',
            jsonb_build_object('text', COALESCE(payload_json::jsonb ->> 'memoryValueText', '')),
            true
        )
        WHERE entity_type = 'memory'
        """
    )
    op.add_column("copilot_memories", sa.Column("memory_value_json", sa.JSON(), nullable=True))
    op.execute(
        """
        UPDATE copilot_memories
        SET memory_value_json = jsonb_build_object('text', COALESCE(memory_value_text, ''))
        """
    )
    op.alter_column("copilot_memories", "memory_value_json", nullable=False)
    op.drop_column("copilot_memories", "memory_value_text")

