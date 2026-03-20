from __future__ import annotations

"""Run pending broadcasts once, without starting the bot polling/webhook loop."""

import asyncio
import logging

from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest

from ..config import BOT_TOKEN
from ..db import init_db, sync_config_tables
from ..utils import setup_logging
from .broadcasts import process_pending_broadcasts

setup_logging()
log = logging.getLogger(__name__)


async def _run_once() -> int:
    """Initialize the minimum application context and dispatch pending broadcasts once."""
    await init_db()
    log.info("Database schema ensured")

    await sync_config_tables()
    log.info("Config tables synced from CSV files")

    httpx_request = HTTPXRequest(
        connect_timeout=20.0,
        read_timeout=20.0,
        write_timeout=20.0,
        pool_timeout=5.0,
    )

    application = ApplicationBuilder().token(BOT_TOKEN).request(httpx_request).build()
    await application.initialize()
    try:
        processed_count = await process_pending_broadcasts(application)
        log.info("Broadcast one-shot run completed. Processed %s broadcast(s)", processed_count)
        return processed_count
    finally:
        await application.shutdown()


def main() -> None:
    """Entry point for manual or external one-shot broadcast execution."""
    asyncio.run(_run_once())


if __name__ == "__main__":
    main()
