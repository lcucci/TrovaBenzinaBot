"""Broadcast repository: claim, recipient resolution and finalization helpers."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, func, or_, select, update

from ..models import BroadcastMessage, Language, User
from ..models.broadcast_message import (
    BROADCAST_STATUS_FAILED,
    BROADCAST_STATUS_PARTIAL_FAILED,
    BROADCAST_STATUS_PENDING,
    BROADCAST_STATUS_PROCESSING,
    BROADCAST_STATUS_SENT,
)
from ..session import AsyncSession
from ...config import DEFAULT_LANGUAGE

MAX_ERROR_LENGTH = 1000


def _compact_error(message: Optional[str]) -> Optional[str]:
    """Normalize and trim error text before storing it in the database."""
    if not message:
        return None
    normalized = " ".join(str(message).split())
    return normalized[:MAX_ERROR_LENGTH]


async def claim_pending_broadcasts(limit: Optional[int] = None) -> list[BroadcastMessage]:
    """Atomically claim pending broadcast rows and mark them as processing."""
    async with AsyncSession() as session:
        async with session.begin():
            stmt = (
                select(BroadcastMessage.id)
                .where(BroadcastMessage.status == BROADCAST_STATUS_PENDING)
                .where(BroadcastMessage.del_ts.is_(None))
                .order_by(BroadcastMessage.id)
                .with_for_update(skip_locked=True)
            )
            if limit is not None:
                stmt = stmt.limit(limit)

            broadcast_ids = list((await session.execute(stmt)).scalars().all())
            if not broadcast_ids:
                return []

            await session.execute(
                update(BroadcastMessage)
                .where(BroadcastMessage.id.in_(broadcast_ids))
                .values(
                    status=BROADCAST_STATUS_PROCESSING,
                    sent_at=None,
                    target_count=0,
                    sent_count=0,
                    failed_count=0,
                    last_error=None,
                    upd_ts=func.now(),
                )
            )

            rows = await session.execute(
                select(BroadcastMessage)
                .where(BroadcastMessage.id.in_(broadcast_ids))
                .order_by(BroadcastMessage.id)
            )
            return rows.scalars().all()


async def get_broadcast_recipient_tg_ids(language_code: str) -> list[int]:
    """Return Telegram user IDs eligible for a language-specific broadcast."""
    normalized_language_code = (language_code or "").strip()
    if not normalized_language_code:
        return []

    async with AsyncSession() as session:
        stmt = (
            select(User.tg_id)
            .select_from(User)
            .outerjoin(Language, User.language_id == Language.id)
            .where(User.del_ts.is_(None))
        )

        if normalized_language_code == DEFAULT_LANGUAGE:
            stmt = stmt.where(
                or_(
                    User.language_id.is_(None),
                    and_(
                        Language.code == normalized_language_code,
                        Language.del_ts.is_(None),
                    ),
                )
            )
        else:
            stmt = stmt.where(
                Language.code == normalized_language_code,
                Language.del_ts.is_(None),
            )

        rows = await session.execute(stmt.distinct().order_by(User.tg_id))
        return rows.scalars().all()


async def finalize_broadcast_message(
        broadcast_id: int,
        target_count: int,
        sent_count: int,
        failed_count: int,
        *,
        fatal_error: Optional[str] = None,
        last_error: Optional[str] = None,
) -> None:
    """Persist final delivery counters and terminal status for a broadcast."""
    if fatal_error:
        status = BROADCAST_STATUS_FAILED
        sent_at = None
        error_text = _compact_error(fatal_error)
    else:
        status = BROADCAST_STATUS_PARTIAL_FAILED if failed_count else BROADCAST_STATUS_SENT
        sent_at = func.now()
        error_text = _compact_error(last_error)

    async with AsyncSession() as session:
        await session.execute(
            update(BroadcastMessage)
            .where(BroadcastMessage.id == broadcast_id)
            .values(
                status=status,
                target_count=target_count,
                sent_count=sent_count,
                failed_count=failed_count,
                sent_at=sent_at,
                last_error=error_text,
                upd_ts=func.now(),
            )
        )
        await session.commit()
