"""Admin-only command handler to process pending broadcasts."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..config import BROADCAST_ADMIN_TG_ID
from ..core.broadcasts import process_pending_broadcasts
from ..db import get_user_language_code_by_tg_id
from ..i18n import t

__all__ = ["broadcast_ep", "broadcast_handler"]

log = logging.getLogger(__name__)


async def broadcast_ep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger broadcast processing for the configured admin account only."""
    message = update.effective_message
    user = update.effective_user
    user_id = user.id if user else None

    if message is None:
        return

    if BROADCAST_ADMIN_TG_ID <= 0:
        log.warning("/broadcast requested but BROADCAST_ADMIN_TG_ID is not configured")
        await message.reply_text("Broadcast admin is not configured.")
        return

    if user_id != BROADCAST_ADMIN_TG_ID:
        log.warning("Unauthorized /broadcast attempt from tg_id=%s", user_id)
        lang = await get_user_language_code_by_tg_id(user_id) if user_id else None
        await message.reply_html(t("unknown_command_hint", lang=lang))
        return

    await message.reply_text("Processing pending broadcast messages...")

    try:
        processed_count = await process_pending_broadcasts(context.application)
    except Exception:
        log.exception("Unhandled error while processing /broadcast command")
        await message.reply_text("Broadcast processing failed. Check logs.")
        return

    suffix = "message" if processed_count == 1 else "messages"
    await message.reply_text(f"Processed {processed_count} pending broadcast {suffix}.")


broadcast_handler = CommandHandler("broadcast", broadcast_ep)
