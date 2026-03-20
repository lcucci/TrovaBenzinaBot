from __future__ import annotations

"""Broadcast entity manually managed from the database."""

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import TimestampMixin

BROADCAST_STATUS_PENDING = "PENDING"
BROADCAST_STATUS_PROCESSING = "PROCESSING"
BROADCAST_STATUS_SENT = "SENT"
BROADCAST_STATUS_PARTIAL_FAILED = "PARTIAL_FAILED"
BROADCAST_STATUS_FAILED = "FAILED"
BROADCAST_STATUS_CANCELLED = "CANCELLED"

BROADCAST_STATUSES = (
    BROADCAST_STATUS_PENDING,
    BROADCAST_STATUS_PROCESSING,
    BROADCAST_STATUS_SENT,
    BROADCAST_STATUS_PARTIAL_FAILED,
    BROADCAST_STATUS_FAILED,
    BROADCAST_STATUS_CANCELLED,
)

__all__ = [
    "BroadcastMessage",
    "BROADCAST_STATUS_PENDING",
    "BROADCAST_STATUS_PROCESSING",
    "BROADCAST_STATUS_SENT",
    "BROADCAST_STATUS_PARTIAL_FAILED",
    "BROADCAST_STATUS_FAILED",
    "BROADCAST_STATUS_CANCELLED",
    "BROADCAST_STATUSES",
]


class BroadcastMessage(TimestampMixin, Base):
    """A manually managed broadcast targeted at one language."""

    __tablename__ = "broadcast_messages"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'SENT', 'PARTIAL_FAILED', 'FAILED', 'CANCELLED')",
            name="ck_broadcast_messages_status",
        ),
        CheckConstraint("target_count >= 0", name="ck_broadcast_messages_target_count_nonneg"),
        CheckConstraint("sent_count >= 0", name="ck_broadcast_messages_sent_count_nonneg"),
        CheckConstraint("failed_count >= 0", name="ck_broadcast_messages_failed_count_nonneg"),
        CheckConstraint(
            "sent_count + failed_count <= target_count",
            name="ck_broadcast_messages_delivery_counts",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    language_code: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("dom_languages.code"),
        nullable=False,
        index=True,
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=BROADCAST_STATUS_PENDING,
        server_default=text("'PENDING'"),
        index=True,
    )
    target_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    sent_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            "BroadcastMessage("
            f"id={self.id}, sent_at={self.sent_at}, language_code={self.language_code}, "
            f"status={self.status}, target_count={self.target_count}, "
            f"sent_count={self.sent_count}, failed_count={self.failed_count})"
        )
