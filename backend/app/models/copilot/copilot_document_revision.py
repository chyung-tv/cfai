from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CopilotDocumentRevision(Base):
    __tablename__ = "copilot_document_revisions"
    __table_args__ = (
        CheckConstraint(
            "author_type IN ('agent','user','system')",
            name="ck_copilot_document_revisions_author_type",
        ),
        Index("ix_copilot_document_revisions_doc_created_at", "doc_key", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    doc_key: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("copilot_canonical_documents.doc_key", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_revision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("copilot_document_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    base_revision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("copilot_document_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    full_content: Mapped[str] = mapped_column(Text, nullable=False)
    patch_text: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    patch_format: Mapped[str] = mapped_column(String(24), nullable=False, server_default="unified_diff")
    author_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="system")
    message: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
