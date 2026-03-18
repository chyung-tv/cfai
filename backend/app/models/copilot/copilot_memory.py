from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CopilotMemory(Base):
    __tablename__ = "copilot_memories"
    __table_args__ = (
        Index("ix_copilot_memories_user_active", "user_id", "is_active"),
        Index("ix_copilot_memories_user_key_active", "user_id", "memory_key", "is_active"),
        Index("ix_copilot_memories_user_updated", "user_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    thread_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("copilot_threads.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_message_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("copilot_messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    memory_key: Mapped[str] = mapped_column(String(160), nullable=False)
    memory_value_text: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    memory_type: Mapped[str] = mapped_column(String(40), nullable=False, server_default="preference")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    rationale: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
