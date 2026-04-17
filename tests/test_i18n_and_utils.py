from __future__ import annotations

import json
import logging
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters

try:
    from tests.support import keyboard_layout, make_context, make_message_update
except ModuleNotFoundError:
    from support import keyboard_layout, make_context, make_message_update

from trovabenzina.i18n import t
from trovabenzina.utils import formatting, logging as logging_utils, routing, telegram


async def _dummy_handler(*args, **kwargs):
    return None


class TranslationTests(unittest.TestCase):
    def test_t_uses_requested_language_and_fallbacks(self):
        self.assertEqual(t("language_name", "en"), "English")
        self.assertEqual(t("choose_search_mode", "en"), "Choose the search type.")
        self.assertEqual(t("route_label", "en"), "Stations along the route")
        self.assertEqual(t("gasoline", "xx"), "Benzina")
        self.assertEqual(t("missing_key", "en"), "missing_key")


class FormattingTests(unittest.TestCase):
    def test_symbol_helpers_and_price_unit_defaults(self):
        self.assertEqual(formatting.symbol_eur(), "€")
        self.assertEqual(formatting.symbol_slash(), "/")
        self.assertEqual(formatting.symbol_liter(), "L")
        self.assertEqual(formatting.symbol_kilo(), "kg")
        self.assertEqual(formatting.format_price_unit(uom="kg"), "€/kg")
        self.assertEqual(formatting.format_price_unit(uom="liter"), "€/L")

    def test_price_and_delta_helpers(self):
        self.assertEqual(formatting.format_price(None, "€/L"), "— €/L")
        self.assertEqual(formatting.format_price(1.8394, "€/L"), "1.839 €/L")
        self.assertEqual(formatting.pct_delta_from_avg(1.8, 2.0), -10)
        self.assertEqual(formatting.pct_delta_from_avg(None, 2.0), 0)

    def test_avg_comparison_text_covers_all_branches(self):
        translations = {
            "equal_average": "equal",
            "below_average": "below",
            "above_average": "above",
        }
        fake_t = lambda key, lang=None: translations[key]

        self.assertEqual(formatting.format_avg_comparison_text(1.5, 1.5, t=fake_t), "equal")
        self.assertEqual(formatting.format_avg_comparison_text(1.5, 2.0, t=fake_t), "25% below")
        self.assertEqual(formatting.format_avg_comparison_text(2.5, 2.0, t=fake_t), "25% above")

    def test_format_date_url_and_radius(self):
        self.assertEqual(
            formatting.format_date("2025-01-08T12:34:56+00:00"),
            "08/01/2025 13:34",
        )
        self.assertEqual(formatting.format_date("not-an-iso-date"), "n/a")
        self.assertEqual(
            formatting.format_directions_url(45.0, 9.0),
            "https://www.google.com/maps/dir/?api=1&destination=45.0,9.0",
        )
        self.assertEqual(formatting.format_radius(5.0), "5")
        self.assertEqual(formatting.format_radius(2.5), "2.5")


class TelegramUtilsTests(unittest.IsolatedAsyncioTestCase):
    def test_inline_keyboard_helpers_build_expected_layout(self):
        grid = telegram.inline_kb(
            [("One", "cb1"), ("Two", "cb2"), ("Three", "cb3")],
            per_row=2,
        )
        self.assertEqual(
            [[(button.text, button.callback_data) for button in row] for row in grid],
            [[("One", "cb1"), ("Two", "cb2")], [("Three", "cb3")]],
        )

        menu = telegram.inline_menu_from_map({"it": "Italiano", "en": "English"}, "lang", per_row=1)
        self.assertEqual(
            [[(button.text, button.callback_data) for button in row] for row in menu],
            [[("Italiano", "lang_it")], [("English", "lang_en")]],
        )

        with_back = telegram.with_back_row(menu, "back")
        self.assertEqual(
            [[(button.text, button.callback_data) for button in row] for row in with_back][-1],
            [("↩", "back")],
        )

    def test_inline_keyboard_rejects_invalid_row_size(self):
        with self.assertRaises(ValueError):
            telegram.inline_kb([("Only", "cb")], per_row=0)

    async def test_profile_message_memory_helpers(self):
        context = make_context()
        telegram.remember_profile_message(context, 321, 654)
        self.assertEqual(context.chat_data["profile_msg"], {"chat_id": 321, "message_id": 654})

        await telegram.delete_last_profile_message(context)
        context.bot.delete_message.assert_awaited_once_with(chat_id=321, message_id=654)
        self.assertNotIn("profile_msg", context.chat_data)

    async def test_delete_last_profile_message_ignores_missing_or_deleted_messages(self):
        context = make_context(
            bot=type("Bot", (), {"delete_message": AsyncMock(side_effect=RuntimeError("gone"))})(),
            chat_data={"profile_msg": {"chat_id": 1, "message_id": 2}},
        )
        await telegram.delete_last_profile_message(context)
        self.assertNotIn("profile_msg", context.chat_data)


class RoutingTests(unittest.IsolatedAsyncioTestCase):
    def test_extract_cmd_normalizes_command(self):
        update = make_message_update(text="/Search@TestBot extra")
        self.assertEqual(routing._extract_cmd(update), "/search")

    async def test_reroute_command_keeps_state_for_start_and_restart(self):
        for command in ("/start", "/restart"):
            with self.subTest(command=command):
                update = make_message_update(text=command)
                context = make_context(chat_data={"current_state": 77})
                state = await routing.reroute_command(update, context)
                self.assertEqual(state, 77)
                context.bot.delete_message.assert_not_awaited()

    async def test_reroute_command_deletes_saved_profile_message_and_dispatches(self):
        update = make_message_update(text="/search")
        context = make_context(chat_data={"profile_msg": {"chat_id": 11, "message_id": 22}})
        with patch("trovabenzina.handlers.search.search_ep", new=AsyncMock()) as search_ep:
            state = await routing.reroute_command(update, context)

        self.assertEqual(state, ConversationHandler.END)
        context.bot.delete_message.assert_awaited_once_with(chat_id=11, message_id=22)
        search_ep.assert_awaited_once_with(update, context)

    async def test_reroute_command_dispatches_profile_help_and_statistics(self):
        scenarios = [
            ("/profile", "trovabenzina.handlers.profile.profile_ep"),
            ("/help", "trovabenzina.handlers.help.help_ep"),
            ("/statistics", "trovabenzina.handlers.statistics.statistics_ep"),
        ]
        for command, target in scenarios:
            with self.subTest(command=command):
                update = make_message_update(text=command)
                context = make_context()
                with patch(target, new=AsyncMock()) as endpoint:
                    state = await routing.reroute_command(update, context)
                self.assertEqual(state, ConversationHandler.END)
                endpoint.assert_awaited_once_with(update, context)


class LoggingTests(unittest.TestCase):
    def test_formatter_outputs_json_and_exception_text(self):
        formatter = logging_utils.RailwayLogFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname=__file__,
                lineno=10,
                msg="failed",
                args=(),
                exc_info=sys.exc_info(),
            )

        payload = json.loads(formatter.format(record))
        self.assertEqual(payload["level"], "error")
        self.assertEqual(payload["name"], "test.logger")
        self.assertEqual(payload["message"], "failed")
        self.assertIn("ValueError: boom", payload["exc_info"])

    def test_setup_logging_replaces_root_handlers(self):
        root = logging.getLogger()
        original_handlers = list(root.handlers)
        self.addCleanup(
            lambda: [root.addHandler(handler) for handler in original_handlers if handler not in root.handlers])

        stale_handler = logging.StreamHandler()
        root.addHandler(stale_handler)

        with patch.object(logging_utils, "LOG_LEVEL", "DEBUG"):
            logging_utils.setup_logging(default_level=logging.INFO)

        self.assertTrue(root.handlers)
        self.assertNotIn(stale_handler, root.handlers)
        self.assertEqual(root.level, logging.DEBUG)
        self.assertIsInstance(root.handlers[0].formatter, logging_utils.RailwayLogFormatter)

    def test_describe_handles_supported_handler_types(self):
        command = CommandHandler("start", _dummy_handler)
        callback = CallbackQueryHandler(_dummy_handler, pattern=r"^ok$")
        message = MessageHandler(filters.TEXT, _dummy_handler)
        conversation = ConversationHandler(entry_points=[command], states={}, fallbacks=[])

        self.assertEqual(logging_utils.describe(command), "CommandHandler(commands=['start'])")
        self.assertEqual(logging_utils.describe(callback), "CallbackQueryHandler(pattern='^ok$')")
        self.assertIn("MessageHandler(filters=", logging_utils.describe(message))
        self.assertEqual(
            logging_utils.describe(conversation),
            "ConversationHandler(entry_points=['/start'])",
        )
        self.assertTrue(logging_utils.describe(Mock()).startswith("Mock("))


if __name__ == "__main__":
    unittest.main()
