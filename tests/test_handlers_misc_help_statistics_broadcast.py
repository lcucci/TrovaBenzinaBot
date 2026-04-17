from __future__ import annotations

import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

try:
    from tests.support import keyboard_layout, make_callback_update, make_context, make_message_update
except ModuleNotFoundError:
    from support import keyboard_layout, make_callback_update, make_context, make_message_update

from trovabenzina.handlers import broadcast, help as help_handler, misc, statistics
from trovabenzina.i18n import t


class MiscAndHelpHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_handle_unrecognized_message_uses_translated_hint(self):
        update = make_message_update(text="hello")
        context = make_context()

        with patch.object(misc, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")):
            await misc.handle_unrecognized_message(update, context)

        update.effective_message.reply_html.assert_awaited_once_with(t("unknown_message_hint", lang="en"))

    async def test_handle_unknown_command_uses_translated_hint(self):
        update = make_message_update(text="/oops")
        context = make_context()

        with patch.object(misc, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")):
            await misc.handle_unknown_command(update, context)

        update.effective_message.reply_html.assert_awaited_once_with(t("unknown_command_hint", lang="en"))

    async def test_help_ep_sends_localized_help_text(self):
        update = make_message_update(text="/help")
        context = make_context()

        with patch.object(help_handler, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")):
            await help_handler.help_ep(update, context)

        update.message.reply_text.assert_awaited_once_with(
            t("help", "en") + t("disclaimer", "en"),
            parse_mode=help_handler.ParseMode.HTML,
        )


class StatisticsHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_statistics_ep_handles_missing_data(self):
        update = make_message_update(text="/statistics")
        context = make_context()

        with (
            patch.object(statistics, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(statistics, "get_user_stats", new=AsyncMock(return_value=[])),
        ):
            await statistics.statistics_ep(update, context)

        update.effective_message.reply_text.assert_awaited_once_with(t("no_statistics", "en"))

    async def test_statistics_ep_renders_blocks_and_reset_button(self):
        update = make_message_update(text="/statistics")
        context = make_context()
        stats_rows = [
            {
                "fuel_id": 1,
                "fuel_name": "gasoline",
                "num_searches": 4,
                "num_stations": 12,
                "avg_eur_save_per_unit": Decimal("0.100"),
                "avg_pct_save": Decimal("0.05"),
                "estimated_annual_save_eur": Decimal("70.00"),
            },
            {
                "fuel_id": 3,
                "fuel_name": "cng",
                "num_searches": 2,
                "num_stations": 6,
                "avg_eur_save_per_unit": Decimal("0.050"),
                "avg_pct_save": Decimal("0.03"),
                "estimated_annual_save_eur": Decimal("25.00"),
            },
        ]
        fuels = {
            1: SimpleNamespace(uom="L", avg_consumption_per_100km=Decimal("7.0")),
            3: SimpleNamespace(uom="kg", avg_consumption_per_100km=Decimal("4.0")),
        }

        with (
            patch.object(statistics, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(statistics, "get_user_stats", new=AsyncMock(return_value=stats_rows)),
            patch.object(statistics, "get_fuels_by_ids_map", new=AsyncMock(return_value=fuels)),
        ):
            await statistics.statistics_ep(update, context)

        args = update.effective_message.reply_text.await_args
        self.assertIn("Gasoline statistics", args.args[0])
        self.assertIn("CNG statistics", args.args[0])
        self.assertIn("7.0L every 100km", args.args[0])
        self.assertIn("4.0kg every 100km", args.args[0])
        self.assertEqual(
            keyboard_layout(args.kwargs["reply_markup"]),
            [[("Reset statistics ♻️", "reset_stats")]],
        )

    async def test_reset_stats_callback_soft_deletes_searches(self):
        update = make_callback_update(data="reset_stats")
        context = make_context()

        with (
            patch.object(statistics, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(statistics, "soft_delete_user_searches_by_tg_id", new=AsyncMock()) as delete_stats,
        ):
            await statistics.reset_stats_cb(update, context)

        update.callback_query.answer.assert_awaited_once()
        delete_stats.assert_awaited_once_with(1)
        update.callback_query.edit_message_text.assert_awaited_once_with(t("statistics_reset", "en"))


class BroadcastHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_broadcast_ep_returns_early_without_message(self):
        update = SimpleNamespace(effective_message=None, effective_user=SimpleNamespace(id=1))
        context = make_context()
        await broadcast.broadcast_ep(update, context)

    async def test_broadcast_ep_requires_configured_admin(self):
        update = make_message_update(text="/broadcast")
        context = make_context()

        with patch.object(broadcast, "BROADCAST_ADMIN_TG_ID", 0):
            await broadcast.broadcast_ep(update, context)

        update.effective_message.reply_text.assert_awaited_once_with("Broadcast admin is not configured.")

    async def test_broadcast_ep_rejects_unauthorized_users(self):
        update = make_message_update(text="/broadcast", user_id=999)
        context = make_context()

        with (
            patch.object(broadcast, "BROADCAST_ADMIN_TG_ID", 123),
            patch.object(broadcast, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
        ):
            await broadcast.broadcast_ep(update, context)

        update.effective_message.reply_html.assert_awaited_once_with(t("unknown_command_hint", lang="en"))

    async def test_broadcast_ep_processes_pending_messages(self):
        update = make_message_update(text="/broadcast", user_id=123)
        context = make_context()

        with (
            patch.object(broadcast, "BROADCAST_ADMIN_TG_ID", 123),
            patch.object(broadcast, "process_pending_broadcasts", new=AsyncMock(return_value=1)) as process_pending,
        ):
            await broadcast.broadcast_ep(update, context)

        self.assertEqual(update.effective_message.reply_text.await_count, 2)
        self.assertEqual(update.effective_message.reply_text.await_args_list[0].args[0],
                         "Processing pending broadcast messages...")
        self.assertEqual(update.effective_message.reply_text.await_args_list[1].args[0],
                         "Processed 1 pending broadcast message.")
        process_pending.assert_awaited_once_with(context.application)

    async def test_broadcast_ep_reports_processing_failures(self):
        update = make_message_update(text="/broadcast", user_id=123)
        context = make_context()

        with (
            patch.object(broadcast, "BROADCAST_ADMIN_TG_ID", 123),
            patch.object(broadcast, "process_pending_broadcasts", new=AsyncMock(side_effect=RuntimeError("boom"))),
        ):
            await broadcast.broadcast_ep(update, context)

        self.assertEqual(update.effective_message.reply_text.await_args_list[-1].args[0],
                         "Broadcast processing failed. Check logs.")


if __name__ == "__main__":
    unittest.main()
