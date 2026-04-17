from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from telegram.error import RetryAfter, TelegramError

from trovabenzina.config import settings as config_settings
from trovabenzina.core import bot, broadcast_runner, broadcasts
from trovabenzina.db.models import BroadcastMessage


class FakeApplication:
    def __init__(self):
        self.bot = SimpleNamespace(send_message=AsyncMock())
        self.handlers: dict[int, list[object]] = {}
        self.added_handlers: list[tuple[object, int]] = []
        self.run_polling = Mock()
        self.run_webhook = Mock()
        self.initialize = AsyncMock()
        self.shutdown = AsyncMock()

    def add_handler(self, handler, group: int = 0) -> None:
        self.added_handlers.append((handler, group))
        self.handlers.setdefault(group, []).append(handler)


class FakeBuilder:
    def __init__(self, application: FakeApplication):
        self.application = application
        self.token_value = None
        self.request_value = None

    def token(self, token: str) -> "FakeBuilder":
        self.token_value = token
        return self

    def request(self, request: object) -> "FakeBuilder":
        self.request_value = request
        return self

    def build(self) -> FakeApplication:
        return self.application


class FakeLoop:
    def __init__(self):
        self.coroutines = []

    def run_until_complete(self, coroutine):
        self.coroutines.append(coroutine)
        return asyncio.run(coroutine)


class BroadcastsTests(unittest.IsolatedAsyncioTestCase):
    def test_format_exception_and_normalize_message_text(self):
        self.assertEqual(broadcasts._format_exception(RuntimeError(" line 1 \n line 2 ")), "line 1 line 2")
        self.assertEqual(broadcasts._normalize_broadcast_message_text("Line 1\\nLine 2"), "Line 1\nLine 2")

    async def test_send_broadcast_message_success_and_failures(self):
        application = SimpleNamespace(bot=SimpleNamespace(send_message=AsyncMock()))
        ok = await broadcasts._send_broadcast_message(application, 123, "Hello\\nWorld")
        self.assertEqual(ok, (True, None))
        application.bot.send_message.assert_awaited_once_with(
            chat_id=123,
            text="Hello\nWorld",
            parse_mode=broadcasts.ParseMode.HTML,
        )

        retry_application = SimpleNamespace(
            bot=SimpleNamespace(send_message=AsyncMock(side_effect=[RetryAfter(1), None])))
        with patch.object(broadcasts.asyncio, "sleep", new=AsyncMock()) as sleep_mock:
            ok = await broadcasts._send_broadcast_message(retry_application, 123, "Retry")
        self.assertEqual(ok, (True, None))
        sleep_mock.assert_awaited_once_with(1)

        failed_retry = SimpleNamespace(
            bot=SimpleNamespace(send_message=AsyncMock(side_effect=[RetryAfter(2), TelegramError("forbidden")]))
        )
        with patch.object(broadcasts.asyncio, "sleep", new=AsyncMock()):
            self.assertEqual(
                await broadcasts._send_broadcast_message(failed_retry, 123, "Retry"),
                (False, "forbidden"),
            )

        direct_failure = SimpleNamespace(
            bot=SimpleNamespace(send_message=AsyncMock(side_effect=TelegramError("bad request"))))
        self.assertEqual(
            await broadcasts._send_broadcast_message(direct_failure, 123, "Hello"),
            (False, "bad request"),
        )

    async def test_deliver_broadcast_updates_counters_and_first_error(self):
        application = SimpleNamespace()
        broadcast_row = BroadcastMessage(id=7, language_code="en", message_text="Hello")

        with (
            patch.object(broadcasts, "get_broadcast_recipient_tg_ids", new=AsyncMock(return_value=[10, 20, 30])),
            patch.object(
                broadcasts,
                "_send_broadcast_message",
                new=AsyncMock(side_effect=[(True, None), (False, "forbidden"), (False, "blocked")]),
            ),
            patch.object(broadcasts, "finalize_broadcast_message", new=AsyncMock()) as finalize,
        ):
            await broadcasts._deliver_broadcast(application, broadcast_row)

        finalize.assert_awaited_once_with(7, 3, 1, 2, last_error="tg_id=20: forbidden")

    async def test_deliver_broadcast_persists_fatal_error(self):
        application = SimpleNamespace()
        broadcast_row = BroadcastMessage(id=8, language_code="it", message_text="Hello")

        with (
            patch.object(broadcasts, "get_broadcast_recipient_tg_ids",
                         new=AsyncMock(side_effect=RuntimeError("db down"))),
            patch.object(broadcasts, "finalize_broadcast_message", new=AsyncMock()) as finalize,
        ):
            await broadcasts._deliver_broadcast(application, broadcast_row)

        finalize.assert_awaited_once_with(8, 0, 0, 0, fatal_error="db down")

    async def test_process_pending_broadcasts_handles_claim_failures_empty_and_non_empty_sets(self):
        with patch.object(broadcasts, "claim_pending_broadcasts", new=AsyncMock(side_effect=RuntimeError("boom"))):
            self.assertEqual(await broadcasts.process_pending_broadcasts(SimpleNamespace()), 0)

        with patch.object(broadcasts, "claim_pending_broadcasts", new=AsyncMock(return_value=[])):
            self.assertEqual(await broadcasts.process_pending_broadcasts(SimpleNamespace()), 0)

        rows = [BroadcastMessage(id=1, language_code="it", message_text="A"),
                BroadcastMessage(id=2, language_code="en", message_text="B")]
        with (
            patch.object(broadcasts, "claim_pending_broadcasts", new=AsyncMock(return_value=rows)),
            patch.object(broadcasts, "_deliver_broadcast", new=AsyncMock()) as deliver,
        ):
            self.assertEqual(await broadcasts.process_pending_broadcasts(SimpleNamespace()), 2)

        deliver.assert_has_awaits(
            [
                unittest.mock.call(unittest.mock.ANY, rows[0]),
                unittest.mock.call(unittest.mock.ANY, rows[1]),
            ]
        )


class BroadcastRunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_once_initializes_app_processes_broadcasts_and_shuts_down(self):
        application = FakeApplication()
        builder = FakeBuilder(application)

        with (
            patch.object(broadcast_runner, "init_db", new=AsyncMock()) as init_db,
            patch.object(broadcast_runner, "sync_config_tables", new=AsyncMock()) as sync_tables,
            patch.object(broadcast_runner, "process_pending_broadcasts",
                         new=AsyncMock(return_value=3)) as process_pending,
            patch.object(broadcast_runner, "ApplicationBuilder", Mock(return_value=builder)),
            patch.object(broadcast_runner, "HTTPXRequest", Mock(return_value="httpx-request")),
            patch.object(broadcast_runner, "BOT_TOKEN", "token-123"),
        ):
            result = await broadcast_runner._run_once()

        self.assertEqual(result, 3)
        init_db.assert_awaited_once()
        sync_tables.assert_awaited_once()
        process_pending.assert_awaited_once_with(application)
        application.initialize.assert_awaited_once()
        application.shutdown.assert_awaited_once()
        self.assertEqual(builder.token_value, "token-123")
        self.assertEqual(builder.request_value, "httpx-request")

    def test_main_runs_async_entrypoint(self):
        def fake_run(coro):
            coro.close()

        with patch.object(broadcast_runner.asyncio, "run", side_effect=fake_run) as run:
            broadcast_runner.main()
        run.assert_called_once()


class BotStartupTests(unittest.TestCase):
    def setUp(self):
        self.language_patch = patch.dict(config_settings.LANGUAGE_MAP, {"old": "xx"}, clear=True)
        self.fuel_patch = patch.dict(config_settings.FUEL_MAP, {"old": "99"}, clear=True)
        self.language_patch.start()
        self.fuel_patch.start()
        self.addCleanup(self.language_patch.stop)
        self.addCleanup(self.fuel_patch.stop)

    def test_main_bootstraps_dependencies_and_runs_polling(self):
        application = FakeApplication()
        builder = FakeBuilder(application)
        loop = FakeLoop()

        with (
            patch.object(bot, "init_db", new=AsyncMock()) as init_db,
            patch.object(bot, "sync_config_tables", new=AsyncMock()) as sync_tables,
            patch.object(bot, "get_language_map", new=AsyncMock(return_value={"English": "en"})),
            patch.object(bot, "get_fuel_map", new=AsyncMock(return_value={"gasoline": "1"})),
            patch.object(bot, "ApplicationBuilder", Mock(return_value=builder)),
            patch.object(bot, "HTTPXRequest", Mock(return_value="httpx-request")),
            patch.object(bot, "BOT_TOKEN", "token-123"),
            patch.object(bot, "TB_MODE", "POLLING"),
            patch.object(bot.asyncio, "new_event_loop", Mock(return_value=loop)),
            patch.object(bot.asyncio, "set_event_loop"),
        ):
            bot.main()

        init_db.assert_awaited_once()
        sync_tables.assert_awaited_once()
        self.assertEqual(config_settings.LANGUAGE_MAP, {"English": "en"})
        self.assertEqual(config_settings.FUEL_MAP, {"gasoline": "1"})
        self.assertEqual(builder.token_value, "token-123")
        self.assertEqual(builder.request_value, "httpx-request")
        self.assertTrue(application.added_handlers)
        self.assertIn(98, application.handlers)
        application.run_polling.assert_called_once_with(
            allowed_updates=None,
            close_loop=False,
            drop_pending_updates=False,
        )

    def test_main_runs_webhook_with_expected_path_and_url(self):
        application = FakeApplication()
        builder = FakeBuilder(application)
        loop = FakeLoop()

        with (
            patch.object(bot, "init_db", new=AsyncMock()),
            patch.object(bot, "sync_config_tables", new=AsyncMock()),
            patch.object(bot, "get_language_map", new=AsyncMock(return_value={})),
            patch.object(bot, "get_fuel_map", new=AsyncMock(return_value={})),
            patch.object(bot, "ApplicationBuilder", Mock(return_value=builder)),
            patch.object(bot, "HTTPXRequest", Mock(return_value="httpx-request")),
            patch.object(bot, "BOT_TOKEN", "token-123"),
            patch.object(bot, "TB_MODE", "WEBHOOK"),
            patch.object(bot, "PORT", 8080),
            patch.object(bot, "WEBHOOK_PATH", "webhook"),
            patch.object(bot, "BASE_URL", "https://example.test"),
            patch.object(bot.asyncio, "new_event_loop", Mock(return_value=loop)),
            patch.object(bot.asyncio, "set_event_loop"),
        ):
            bot.main()

        application.run_webhook.assert_called_once_with(
            listen="0.0.0.0",
            port=8080,
            url_path="webhook",
            webhook_url="https://example.test/webhook",
        )

    def test_main_requires_base_url_in_webhook_mode(self):
        application = FakeApplication()
        builder = FakeBuilder(application)
        loop = FakeLoop()

        with (
            patch.object(bot, "init_db", new=AsyncMock()),
            patch.object(bot, "sync_config_tables", new=AsyncMock()),
            patch.object(bot, "get_language_map", new=AsyncMock(return_value={})),
            patch.object(bot, "get_fuel_map", new=AsyncMock(return_value={})),
            patch.object(bot, "ApplicationBuilder", Mock(return_value=builder)),
            patch.object(bot, "HTTPXRequest", Mock(return_value="httpx-request")),
            patch.object(bot, "TB_MODE", "WEBHOOK"),
            patch.object(bot, "BASE_URL", None),
            patch.object(bot.asyncio, "new_event_loop", Mock(return_value=loop)),
            patch.object(bot.asyncio, "set_event_loop"),
        ):
            with self.assertRaisesRegex(RuntimeError, "BASE_URL"):
                bot.main()


if __name__ == "__main__":
    unittest.main()
