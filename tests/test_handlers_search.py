from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telegram.ext import ConversationHandler

try:
    from tests.support import keyboard_layout, make_callback_update, make_context, make_message_update
except ModuleNotFoundError:
    from support import keyboard_layout, make_callback_update, make_context, make_message_update

from trovabenzina.handlers import search
from trovabenzina.i18n import t
from trovabenzina.utils import (
    STEP_SEARCH_LOCATION,
    STEP_SEARCH_MODE,
    STEP_SEARCH_ROUTE_DESTINATION,
    STEP_SEARCH_ROUTE_ORIGIN,
)


class SearchHandlerTests(unittest.IsolatedAsyncioTestCase):
    def test_message_from_update_works_for_messages_and_callbacks(self):
        message_update = make_message_update(text="/search")
        callback_update = make_callback_update(data="search:r=2.5")

        self.assertIs(search._message_from_update(message_update), message_update.message)
        self.assertIs(search._message_from_update(callback_update), callback_update.callback_query.message)

    async def test_clear_processing_toast_deletes_saved_message_and_ignores_failures(self):
        context = make_context(user_data={"processing_msg_id": 99})
        await search._clear_processing_toast(context, 321)
        context.bot.delete_message.assert_awaited_once_with(321, 99)
        self.assertNotIn("processing_msg_id", context.user_data)

        failing_bot = SimpleNamespace(delete_message=AsyncMock(side_effect=RuntimeError("gone")))
        context = make_context(bot=failing_bot, user_data={"processing_msg_id": 99})
        await search._clear_processing_toast(context, 321)
        self.assertNotIn("processing_msg_id", context.user_data)

    async def test_search_ep_prompts_for_mode_selection(self):
        update = make_message_update(text="/search")
        context = make_context(user_data={"search_lat": 1, "route_origin_lat": 2})

        with patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")):
            state = await search.search_ep(update, context)

        self.assertEqual(state, STEP_SEARCH_MODE)
        self.assertNotIn("search_lat", context.user_data)
        self.assertNotIn("route_origin_lat", context.user_data)
        markup = update.message.reply_text.await_args.kwargs["reply_markup"]
        self.assertEqual(update.message.reply_text.await_args.args[0], t("choose_search_mode", "en"))
        self.assertEqual(
            keyboard_layout(markup),
            [
                [(t("btn_search_zone", "en"), "search:mode:zone")],
                [(t("btn_search_route", "en"), "search:mode:route")],
            ],
        )

    async def test_search_mode_callback_routes_to_zone_or_route_and_deletes_prompt(self):
        scenarios = [
            ("search:mode:zone", STEP_SEARCH_LOCATION, "ask_location"),
            ("search:mode:route", STEP_SEARCH_ROUTE_ORIGIN, "ask_route_origin"),
        ]
        for data, expected_state, expected_key in scenarios:
            with self.subTest(data=data):
                update = make_callback_update(data=data, reply_message=SimpleNamespace(message_id=444))
                context = make_context()

                with patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")):
                    state = await search.search_mode_callback(update, context)

                self.assertEqual(state, expected_state)
                context.bot.delete_message.assert_awaited_once_with(chat_id=100, message_id=444)
                context.bot.send_message.assert_awaited_once_with(
                    chat_id=100,
                    text=t(expected_key, "en"),
                    reply_markup=unittest.mock.ANY,
                )

    async def test_search_receive_location_stores_coordinates_and_starts_search(self):
        location = SimpleNamespace(latitude=45.1, longitude=9.2)
        processing_message = SimpleNamespace(message_id=77)
        update = make_message_update(text=None, location=location, reply_message=processing_message)
        context = make_context()

        with (
            patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(search, "run_search", new=AsyncMock()) as run_search,
        ):
            state = await search.search_receive_location(update, context)

        self.assertEqual(state, ConversationHandler.END)
        self.assertEqual(context.user_data["search_mode"], "zone")
        self.assertEqual(context.user_data["search_lat"], 45.1)
        self.assertEqual(context.user_data["search_lng"], 9.2)
        self.assertEqual(context.user_data["processing_msg_id"], 77)
        self.assertEqual(context.user_data["radius_clicked"], set())
        run_search.assert_awaited_once_with(update, context, radius_km=5.0, show_initial_cta=True)

    async def test_search_receive_text_uses_cache_when_available(self):
        processing_message = SimpleNamespace(message_id=88)
        update = make_message_update(text="Via Roma", reply_message=processing_message)
        context = make_context()

        with (
            patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(search, "_resolve_address_to_coords", new=AsyncMock(return_value=((44.4, 11.1), None))),
            patch.object(search, "run_search", new=AsyncMock()) as run_search,
        ):
            state = await search.search_receive_text(update, context)

        self.assertEqual(state, ConversationHandler.END)
        self.assertEqual(context.user_data["search_mode"], "zone")
        self.assertEqual(context.user_data["search_lat"], 44.4)
        self.assertEqual(context.user_data["search_lng"], 11.1)
        run_search.assert_awaited_once_with(update, context, radius_km=5.0, show_initial_cta=True)

    async def test_search_receive_text_stops_when_address_resolution_fails(self):
        for error_key in ("geocode_cap_reached", "invalid_address", "italy_only"):
            with self.subTest(error_key=error_key):
                processing_message = SimpleNamespace(message_id=90)
                update = make_message_update(text="Via Roma", reply_message=processing_message)
                context = make_context()

                with (
                    patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
                    patch.object(search, "_resolve_address_to_coords", new=AsyncMock(return_value=(None, error_key))),
                    patch.object(search, "_clear_processing_toast", new=AsyncMock()) as clear_toast,
                ):
                    state = await search.search_receive_text(update, context)

                self.assertEqual(state, STEP_SEARCH_LOCATION)
                clear_toast.assert_awaited_once_with(context, 100)
                self.assertEqual(update.message.reply_text.await_args_list[-1].args[0], t(error_key, "en"))

    async def test_route_origin_reasks_only_the_origin_step_on_failure(self):
        update = make_message_update(text="Bad origin", reply_message=SimpleNamespace(message_id=91))
        context = make_context()

        with (
            patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(search, "_resolve_address_to_coords", new=AsyncMock(return_value=(None, "invalid_address"))),
            patch.object(search, "_clear_processing_toast", new=AsyncMock()) as clear_toast,
        ):
            state = await search.search_receive_route_origin(update, context)

        self.assertEqual(state, STEP_SEARCH_ROUTE_ORIGIN)
        clear_toast.assert_awaited_once_with(context, 100)
        self.assertEqual(update.message.reply_text.await_args_list[-2].args[0], t("invalid_address", "en"))
        self.assertEqual(update.message.reply_text.await_args_list[-1].args[0], t("ask_route_origin", "en"))

    async def test_route_origin_stores_coordinates_and_prompts_destination(self):
        update = make_message_update(text="Milano", reply_message=SimpleNamespace(message_id=92))
        context = make_context()

        with (
            patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(search, "_resolve_address_to_coords", new=AsyncMock(return_value=((45.4, 9.1), None))),
            patch.object(search, "_clear_processing_toast", new=AsyncMock()) as clear_toast,
        ):
            state = await search.search_receive_route_origin(update, context)

        self.assertEqual(state, STEP_SEARCH_ROUTE_DESTINATION)
        clear_toast.assert_awaited_once_with(context, 100)
        self.assertEqual(context.user_data["search_mode"], "route")
        self.assertEqual(context.user_data["route_origin_lat"], 45.4)
        self.assertEqual(context.user_data["route_origin_lng"], 9.1)
        self.assertEqual(update.message.reply_text.await_args_list[-1].args[0], t("ask_route_destination", "en"))

    async def test_route_destination_reasks_only_the_destination_step_on_failure(self):
        update = make_message_update(text="Bad destination", reply_message=SimpleNamespace(message_id=93))
        context = make_context(user_data={"route_origin_lat": 45.4, "route_origin_lng": 9.1})

        with (
            patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(search, "_resolve_address_to_coords", new=AsyncMock(return_value=(None, "italy_only"))),
            patch.object(search, "_clear_processing_toast", new=AsyncMock()) as clear_toast,
        ):
            state = await search.search_receive_route_destination(update, context)

        self.assertEqual(state, STEP_SEARCH_ROUTE_DESTINATION)
        clear_toast.assert_awaited_once_with(context, 100)
        self.assertEqual(update.message.reply_text.await_args_list[-2].args[0], t("italy_only", "en"))
        self.assertEqual(update.message.reply_text.await_args_list[-1].args[0], t("ask_route_destination", "en"))

    async def test_route_destination_runs_route_search_when_geocoding_succeeds(self):
        update = make_message_update(text="Roma", reply_message=SimpleNamespace(message_id=94))
        context = make_context(user_data={"route_origin_lat": 45.4, "route_origin_lng": 9.1})

        with (
            patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(search, "_resolve_address_to_coords", new=AsyncMock(return_value=((41.9, 12.5), None))),
            patch.object(search, "run_route_search", new=AsyncMock()) as run_route_search,
        ):
            state = await search.search_receive_route_destination(update, context)

        self.assertEqual(state, ConversationHandler.END)
        self.assertEqual(context.user_data["search_mode"], "route")
        self.assertEqual(context.user_data["route_destination_lat"], 41.9)
        self.assertEqual(context.user_data["route_destination_lng"], 12.5)
        run_route_search.assert_awaited_once_with(update, context)

    async def test_run_search_aborts_when_session_coordinates_are_missing(self):
        update = make_message_update(text="/search")
        context = make_context(user_data={})

        with (
            patch.object(search, "get_user", new=AsyncMock(return_value=("1", "en"))),
            patch.object(search, "_clear_processing_toast", new=AsyncMock()) as clear_toast,
        ):
            await search.run_search(update, context, radius_km=5.0)

        clear_toast.assert_awaited_once_with(context, 100)
        update.message.reply_text.assert_awaited_once_with(t("search_session_expired", "en"))

    async def test_run_search_handles_unavailable_backend(self):
        update = make_message_update(text="/search")
        context = make_context(user_data={"search_lat": 45.0, "search_lng": 9.0})

        with (
            patch.object(search, "get_user", new=AsyncMock(return_value=("1", "en"))),
            patch.object(search, "get_uom_by_code", new=AsyncMock(return_value="L")),
            patch.object(search, "get_fuel_name_by_code", new=AsyncMock(return_value="gasoline")),
            patch.object(search, "search_stations", new=AsyncMock(return_value=None)),
            patch.object(search, "save_search", new=AsyncMock()) as save_search,
            patch.object(search, "_clear_processing_toast", new=AsyncMock()) as clear_toast,
        ):
            await search.run_search(update, context, radius_km=5.0)

        clear_toast.assert_awaited_once()
        update.message.reply_text.assert_awaited_once_with(t("search_temporarily_unavailable", "en"))
        save_search.assert_awaited_once_with(1, "1", 5.0, 0, None, None, search_type="zone")

    async def test_run_search_formats_results_builds_cta_and_persists_statistics(self):
        update = make_message_update(text="/search")
        context = make_context(user_data={"search_lat": 45.0, "search_lng": 9.0})
        payload = {
            "results": [
                {
                    "id": 1,
                    "brand": "IP",
                    "name": "Self Winner",
                    "address": "Via Roma 1",
                    "insertDate": "2025-01-01T10:00:00Z",
                    "location": {"lat": 45.1, "lng": 9.1},
                    "fuels": [{"fuelId": 1, "price": 1.7, "isSelf": True}],
                },
                {
                    "id": 2,
                    "brand": "Q8",
                    "name": "Served Tie",
                    "address": "Via Roma 2",
                    "insertDate": "2025-01-01T10:00:00Z",
                    "location": {"lat": 45.2, "lng": 9.2},
                    "fuels": [{"fuelId": 1, "price": 1.7, "isSelf": False}],
                },
                {
                    "id": 3,
                    "brand": "Esso",
                    "name": "Missing Address",
                    "address": "",
                    "insertDate": "2025-01-01T11:00:00Z",
                    "location": {"lat": 45.3, "lng": 9.3},
                    "fuels": [{"fuelId": 1, "price": 1.8, "isSelf": True}],
                },
                {
                    "id": 4,
                    "brand": "Tamoil",
                    "name": "Above Average",
                    "address": "Via Roma 4",
                    "insertDate": "2025-01-01T12:00:00Z",
                    "location": {"lat": 45.4, "lng": 9.4},
                    "fuels": [{"fuelId": 1, "price": 2.1, "isSelf": True}],
                },
            ]
        }

        with (
            patch.object(search, "get_user", new=AsyncMock(return_value=("1", "en"))),
            patch.object(search, "get_uom_by_code", new=AsyncMock(return_value="L")),
            patch.object(search, "get_fuel_name_by_code", new=AsyncMock(return_value="gasoline")),
            patch.object(search, "search_stations", new=AsyncMock(return_value=payload)),
            patch.object(search, "get_station_address",
                         new=AsyncMock(return_value="Recovered address")) as get_station_address,
            patch.object(search, "save_search", new=AsyncMock()) as save_search,
            patch.object(search, "_clear_processing_toast", new=AsyncMock()),
        ):
            await search.run_search(update, context, radius_km=5.0, show_initial_cta=True)

        reply_text = update.message.reply_text.await_args.args[0]
        markup = update.message.reply_text.await_args.kwargs["reply_markup"]
        self.assertIn("Self Winner", reply_text)
        self.assertIn("Missing Address", reply_text)
        self.assertIn("Recovered address", reply_text)
        self.assertNotIn("Served Tie", reply_text)
        self.assertNotIn("Above Average", reply_text)
        self.assertEqual(
            keyboard_layout(markup),
            [
                [("Repeat search with 2.5 km radius 🔄", "search:r=2.5")],
                [("Repeat search with 7.5 km radius 🔄", "search:r=7.5")],
            ],
        )
        get_station_address.assert_awaited_once_with(3)
        save_search.assert_awaited_once_with(1, "1", 5.0, 3, 1.867, 1.7, search_type="zone")

    async def test_run_route_search_formats_results_and_persists_route_statistics(self):
        update = make_message_update(text="/search")
        context = make_context(
            user_data={
                "route_origin_lat": 45.0,
                "route_origin_lng": 9.0,
                "route_destination_lat": 44.5,
                "route_destination_lng": 11.3,
            }
        )
        payload = {
            "results": [
                {
                    "id": 1,
                    "brand": "IP",
                    "name": "Route Winner",
                    "address": "Via Milano 1",
                    "insertDate": "2025-01-01T10:00:00Z",
                    "location": {"lat": 45.1, "lng": 9.1},
                    "fuels": [{"fuelId": 1, "price": 1.71, "isSelf": True}],
                },
                {
                    "id": 2,
                    "brand": "Q8",
                    "name": "Served Tie",
                    "address": "Via Milano 2",
                    "insertDate": "2025-01-01T10:00:00Z",
                    "location": {"lat": 45.2, "lng": 9.2},
                    "fuels": [{"fuelId": 1, "price": 1.71, "isSelf": False}],
                },
                {
                    "id": 3,
                    "brand": "Esso",
                    "name": "Runner Up",
                    "address": "Via Milano 3",
                    "insertDate": "2025-01-01T11:00:00Z",
                    "location": {"lat": 45.3, "lng": 9.3},
                    "fuels": [{"fuelId": 1, "price": 1.73, "isSelf": True}],
                },
            ]
        }

        with (
            patch.object(search, "get_user", new=AsyncMock(return_value=("1", "en"))),
            patch.object(search, "get_uom_by_code", new=AsyncMock(return_value="L")),
            patch.object(search, "get_fuel_name_by_code", new=AsyncMock(return_value="gasoline")),
            patch.object(search, "search_route_stations", new=AsyncMock(return_value=payload)),
            patch.object(search, "save_search", new=AsyncMock()) as save_search,
            patch.object(search, "_clear_processing_toast", new=AsyncMock()),
        ):
            await search.run_route_search(update, context)

        reply_text = update.message.reply_text.await_args.args[0]
        self.assertIn(t("route_label", "en"), reply_text)
        self.assertIn("Route Winner", reply_text)
        self.assertNotIn("Runner Up", reply_text)
        self.assertNotIn("Served Tie", reply_text)
        self.assertIsNone(update.message.reply_text.await_args.kwargs.get("reply_markup"))
        save_search.assert_awaited_once_with(1, "1", None, 2, 1.72, 1.71, search_type="route")

    async def test_radius_callback_blocks_double_taps(self):
        update = make_callback_update(data="search:r=2.5")
        context = make_context(user_data={"radius_processing": True})

        with patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")):
            await search.radius_callback(update, context)

        update.callback_query.answer.assert_awaited_once_with(t("please_wait", "en"))
        update.callback_query.edit_message_reply_markup.assert_not_awaited()

    async def test_radius_callback_runs_followup_search_and_tracks_clicked_radii(self):
        update = make_callback_update(data="search:r=2.5", reply_message=SimpleNamespace(message_id=101))
        context = make_context(user_data={"radius_processing": False, "radius_clicked": set()})

        with (
            patch.object(search, "get_user_language_code_by_tg_id", new=AsyncMock(return_value="en")),
            patch.object(search, "run_search", new=AsyncMock()) as run_search,
        ):
            await search.radius_callback(update, context)

        update.callback_query.answer.assert_awaited_once_with()
        update.callback_query.edit_message_reply_markup.assert_awaited_once_with(reply_markup=None)
        update.callback_query.message.reply_text.assert_awaited_once()
        self.assertEqual(context.user_data["processing_msg_id"], 101)
        self.assertEqual(context.user_data["radius_clicked"], {"2.5"})
        self.assertFalse(context.user_data["radius_processing"])
        run_search.assert_awaited_once_with(update, context, radius_km=2.5, followup_offer_radius=7.5)


if __name__ == "__main__":
    unittest.main()
