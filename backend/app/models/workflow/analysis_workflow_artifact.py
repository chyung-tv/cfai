from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisWorkflowArtifact(Base):
    __tablename__ = "analysis_workflow_artifacts"
    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "artifact_type",
            "artifact_version",
            name="uq_analysis_workflow_artifact_versioned",
        ),
        Index(
            "ix_analysis_workflow_artifacts_workflow_type",
            "workflow_id",
            "artifact_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    artifact_version: Mapped[str] = mapped_column(String(40), nullable=False, server_default="v1")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    produced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
