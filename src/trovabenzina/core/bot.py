import asyncio
import logging

from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram.request import HTTPXRequest

from ..config import (
    BOT_TOKEN,
    TB_MODE,
    PORT,
    BASE_URL,
    WEBHOOK_PATH,
)
from ..db import (
    init_db,
    sync_config_tables,
    get_fuel_map,
    get_language_map,
)
from ..handlers import (
    start_handler,
    help_handler,
    profile_handler,
    search_handler,
    radius_callback_handler,
    statistics_handler,
    broadcast_handler,
    handle_unknown_command,
)
from ..utils import setup_logging, describe

KNOWN_CMDS_RE = r"^/(start|search|profile|statistics|help|broadcast)(?:@\w+)?(?:\s|$)"

# Configure logging (level picked up inside setup_logging if you wired env there)
setup_logging()
log = logging.getLogger(__name__)


def main() -> None:
    """Initialize DB, sync config tables, load maps, register handlers, and run the bot."""
    # Create and set a new async event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # DB bootstrap
    loop.run_until_complete(init_db())
    log.info("Database schema ensured")

    loop.run_until_complete(sync_config_tables())
    log.info("Config tables synced from CSV files")

    # Load mappings for handlers
    language_map = loop.run_until_complete(get_language_map())
    fuel_map = loop.run_until_complete(get_fuel_map())
    from trovabenzina.config.settings import LANGUAGE_MAP, FUEL_MAP
    LANGUAGE_MAP.clear()
    LANGUAGE_MAP.update(language_map)
    FUEL_MAP.clear()
    FUEL_MAP.update(fuel_map)
    log.info("Loaded code maps: %d languages, %d fuels", len(LANGUAGE_MAP), len(FUEL_MAP))

    httpx_request = HTTPXRequest(
        connect_timeout=20.0,
        read_timeout=20.0,
        write_timeout=20.0,
        pool_timeout=5.0,
    )

    app = ApplicationBuilder().token(BOT_TOKEN).request(httpx_request).build()

    # Handlers
    app.add_handler(start_handler)  # /start
    app.add_handler(broadcast_handler)  # /broadcast (admin)
    for handler in statistics_handler:  # /statistics
        app.add_handler(handler)
    app.add_handler(help_handler)  # /help
    app.add_handler(search_handler)  # /search
    app.add_handler(radius_callback_handler)  # callbacks for /search
    app.add_handler(profile_handler)  # /profile
    app.add_handler(
        MessageHandler(filters.COMMAND & ~filters.Regex(KNOWN_CMDS_RE), handle_unknown_command),
        group=98,
    )

    # Debug: registry
    log.debug("=== HANDLER REGISTRY ===")
    for group, handler_list in app.handlers.items():
        for handler in handler_list:
            log.debug("Group %s -> %s", group, describe(handler))

    # Startup mode from config
    mode = TB_MODE.strip().upper()

    if mode == "WEBHOOK":
        port = PORT
        path = WEBHOOK_PATH
        base_url = BASE_URL
        if not base_url:
            raise RuntimeError("TB_MODE=WEBHOOK requires BASE_URL to be set in config.")
        webhook_url = f"{base_url}/{path}"
        log.info("Starting webhook server on 0.0.0.0:%s, url_path=%s -> %s", port, path, webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=base_url,
            webhook_url=webhook_url,
        )
    else:
        log.info("Starting polling (TB_MODE=%s)", mode)
        app.run_polling(
            allowed_updates=None,
            close_loop=False,
            drop_pending_updates=False,
        )


if __name__ == "__main__":
    main()