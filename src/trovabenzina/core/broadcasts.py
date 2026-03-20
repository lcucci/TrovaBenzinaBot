from __future__ import annotations

"""Broadcast delivery helpers."""

import asyncio
import logging
from typing import Optional

from telegram.constants import ParseMode
from telegram.error import RetryAfter, TelegramError
from telegram.ext import Application

from ..db import claim_pending_broadcasts, finalize_broadcast_message, get_broadcast_recipient_tg_ids
from ..db.models import BroadcastMessage

__all__ = ["process_pending_broadcasts"]

log = logging.getLogger(__name__)


def _format_exception(exc: Exception) -> str:
    """Return a compact exception message suitable for logs and DB storage."""
    message = " ".join(str(exc).split())
    return message or exc.__class__.__name__


def _normalize_broadcast_message_text(message_text: str) -> str:
    """Convert escaped newlines from DB content into real line breaks."""
    return (message_text or "").replace("\\n", "\n")


async def _send_broadcast_message(
        application: Application,
        tg_id: int,
        message_text: str,
) -> tuple[bool, Optional[str]]:
    """Send one broadcast message, retrying once on Telegram rate limits."""
    normalized_message_text = _normalize_broadcast_message_text(message_text)
    try:
        await application.bot.send_message(
            chat_id=tg_id,
            text=normalized_message_text,
            parse_mode=ParseMode.HTML,
        )
        return True, None
    except RetryAfter as exc:
        retry_after = getattr(exc, "retry_after", 1)
        if hasattr(retry_after, "total_seconds"):
            retry_delay = max(int(retry_after.total_seconds()), 1)
        else:
            retry_delay = max(int(retry_after), 1)

        log.warning(
            "Rate limit while sending broadcast to tg_id=%s. Retrying in %s seconds.",
            tg_id,
            retry_delay,
        )
        await asyncio.sleep(retry_delay)
        try:
            await application.bot.send_message(
                chat_id=tg_id,
                text=normalized_message_text,
                parse_mode=ParseMode.HTML,
            )
            return True, None
        except TelegramError as retry_exc:
            return False, _format_exception(retry_exc)
        except Exception as retry_exc:  # pragma: no cover - defensive fallback
            return False, _format_exception(retry_exc)
    except TelegramError as exc:
        return False, _format_exception(exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return False, _format_exception(exc)


async def _deliver_broadcast(application: Application, broadcast: BroadcastMessage) -> None:
    """Resolve recipients, send the broadcast and persist final counters."""
    target_count = 0
    sent_count = 0
    failed_count = 0
    first_error = None

    try:
        recipients = await get_broadcast_recipient_tg_ids(broadcast.language_code)
        target_count = len(recipients)

        for tg_id in recipients:
            delivered, error_message = await _send_broadcast_message(
                application,
                tg_id,
                broadcast.message_text,
            )
            if delivered:
                sent_count += 1
                continue

            failed_count += 1
            if first_error is None and error_message is not None:
                first_error = f"tg_id={tg_id}: {error_message}"
    except Exception as exc:
        log.exception("Fatal error while processing broadcast id=%s", broadcast.id)
        await finalize_broadcast_message(
            broadcast.id,
            target_count,
            sent_count,
            failed_count,
            fatal_error=_format_exception(exc),
        )
        return

    await finalize_broadcast_message(
        broadcast.id,
        target_count,
        sent_count,
        failed_count,
        last_error=first_error,
    )
    log.info(
        "Broadcast id=%s completed with status=%s target_count=%s sent_count=%s failed_count=%s",
        broadcast.id,
        "PARTIAL_FAILED" if failed_count else "SENT",
        target_count,
        sent_count,
        failed_count,
    )


async def process_pending_broadcasts(application: Application) -> int:
    """Claim and deliver all pending broadcast rows."""
    try:
        broadcasts = await claim_pending_broadcasts()
    except Exception:
        log.exception("Unable to claim pending broadcast messages")
        return 0

    if not broadcasts:
        log.debug("No pending broadcast messages found")
        return 0

    log.info("Claimed %s pending broadcast message(s)", len(broadcasts))
    for broadcast in broadcasts:
        try:
            await _deliver_broadcast(application, broadcast)
        except Exception:
            log.exception("Unhandled error while finalizing broadcast id=%s", broadcast.id)

    return len(broadcasts)