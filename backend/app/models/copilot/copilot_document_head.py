from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CopilotDocumentHead(Base):
    __tablename__ = "copilot_document_heads"

    doc_key: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("copilot_canonical_documents.doc_key", ondelete="CASCADE"),
        primary_key=True,
    )
    current_revision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("copilot_document_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
