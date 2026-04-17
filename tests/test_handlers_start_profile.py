from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from telegram.ext import ConversationHandler

try:
    from tests.support import keyboard_layout, make_callback_update, make_context, make_message_update
except ModuleNotFoundError:
    from support import keyboard_layout, make_callback_update, make_context, make_message_update

from trovabenzina.handlers import profile, start
from trovabenzina.i18n import t
from trovabenzina.utils import (
    STEP_PROFILE_FUEL,
    STEP_PROFILE_LANGUAGE,
    STEP_PROFILE_MENU,
    STEP_START_FUEL,
    STEP_START_LANGUAGE,
)


class StartHandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.language_patch = patch.dict(start.LANGUAGE_MAP, {"Italiano": "it", "English": "en"}, clear=True)
        self.fuel_patch = patch.dict(start.FUEL_MAP, {"gasoline": "1", "diesel": "2"}, clear=True)
        self.language_patch.start()
        self.fuel_patch.start()
        self.addCleanup(self.language_patch.stop)
        self.addCleanup(self.fuel_patch.stop)

    async def test_start_ep_ends_for_existing_user(self):
        update = make_message_update(text="/start")
        context = make_context()

        with patch.object(start, "get_user", new=AsyncMock(return_value=("1", "en"))):
            state = await start.start_ep(update, context)

        self.assertEqual(state, ConversationHandler.END)
        update.effective_message.reply_text.assert_awaited_once_with(t("user_already_registered", "en"))

    async def test_start_ep_prompts_for_language_for_new_user(self):
        update = make_message_update(text="/start", reply_message=type("Msg", (), {"chat_id": 100, "message_id": 55})())
        context = make_context()

        with patch.object(start, "get_user", new=AsyncMock(return_value=None)):
            state = await start.start_ep(update, context)

        self.assertEqual(state, STEP_START_LANGUAGE)
        update.effective_message.reply_text.assert_awaited_once()
        markup = update.effective_message.reply_text.await_args.kwargs["reply_markup"]
        self.assertEqual(
            keyboard_layout(markup),
            [[("Italiano", "lang_it"), ("English", "lang_en")]],
        )
        self.assertEqual(context.user_data["prev_prompt_id"], 55)

    async def test_language_selection_moves_to_fuel_step(self):
        update = make_callback_update(data="lang_en")
        context = make_context()

        state = await start.language_selected(update, context)

        self.assertEqual(state, STEP_START_FUEL)
        self.assertEqual(context.user_data["lang"], "en")
        update.callback_query.answer.assert_awaited_once()
        markup = update.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual(
            keyboard_layout(markup),
            [[("Gasoline", "fuel_1"), ("Diesel", "fuel_2")], [("↩", "back_lang")]],
        )

    async def test_fuel_selection_persists_profile_and_ends_conversation(self):
        update = make_callback_update(data="fuel_2")
        context = make_context(user_data={"lang": "en"})

        with patch.object(start, "upsert_user", new=AsyncMock()) as upsert_user:
            state = await start.fuel_selected(update, context)

        self.assertEqual(state, ConversationHandler.END)
        upsert_user.assert_awaited_once_with(1, "tester", "2", "en")
        update.callback_query.edit_message_text.assert_awaited_once_with(t("profile_saved", "en"))

    async def test_back_and_repeat_handlers_rebuild_expected_prompts(self):
        update = make_callback_update(data="back_lang")
        context = make_context(user_data={"lang": "en"})

        state = await start.back_to_lang(update, context)
        self.assertEqual(state, STEP_START_LANGUAGE)
        markup = update.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual(keyboard_layout(markup), [[("Italiano", "lang_it"), ("English", "lang_en")]])

        repeat_update = make_message_update(text="invalid",
                                            reply_message=type("Msg", (), {"chat_id": 100, "message_id": 88})())
        repeat_context = make_context(user_data={"lang": "en", "prev_prompt_id": 44})
        state = await start.repeat_fuel_prompt(repeat_update, repeat_context)

        self.assertEqual(state, STEP_START_FUEL)
        repeat_context.bot.delete_message.assert_awaited_once_with(chat_id=100, message_id=44)
        self.assertEqual(repeat_context.user_data["prev_prompt_id"], 88)
        markup = repeat_update.effective_message.reply_text.await_args.kwargs["reply_markup"]
        self.assertEqual(
            keyboard_layout(markup),
            [[("Gasoline", "fuel_1"), ("Diesel", "fuel_2")], [("↩", "back_lang")]],
        )


class ProfileHandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.language_patch = patch.dict(profile.LANGUAGE_MAP, {"Italiano": "it", "English": "en"}, clear=True)
        self.fuel_patch = patch.dict(profile.FUEL_MAP, {"gasoline": "1", "diesel": "2"}, clear=True)
        self.language_patch.start()
        self.fuel_patch.start()
        self.addCleanup(self.language_patch.stop)
        self.addCleanup(self.fuel_patch.stop)

    async def test_get_or_create_defaults_uses_existing_or_bootstraps(self):
        with patch.object(profile, "get_user", new=AsyncMock(return_value=("2", "en"))):
            self.assertEqual(await profile._get_or_create_defaults(1, "tester"), ("2", "en"))

        with (
            patch.object(profile, "get_user", new=AsyncMock(return_value=None)),
            patch.object(profile, "upsert_user", new=AsyncMock()) as upsert_user,
        ):
            self.assertEqual(await profile._get_or_create_defaults(1, "tester"), ("1", "it"))
        upsert_user.assert_awaited_once_with(1, "tester", "1", "it")

    async def test_profile_ep_shows_summary_and_remembers_message(self):
        update = make_message_update(text="/profile",
                                     reply_message=type("Msg", (), {"chat_id": 100, "message_id": 66})())
        context = make_context()

        with (
            patch.object(profile, "delete_last_profile_message", new=AsyncMock()) as delete_last,
            patch.object(profile, "_get_or_create_defaults", new=AsyncMock(return_value=("1", "en"))),
        ):
            state = await profile.profile_ep(update, context)

        self.assertEqual(state, STEP_PROFILE_MENU)
        delete_last.assert_awaited_once_with(context)
        self.assertIn("Language", update.effective_message.reply_text.await_args.args[0])
        self.assertEqual(context.chat_data["profile_msg"], {"chat_id": 100, "message_id": 66})
        self.assertEqual(context.chat_data["current_state"], STEP_PROFILE_MENU)

    async def test_ask_language_and_ask_fuel_render_selection_menus(self):
        lang_update = make_callback_update(data="profile_set_language")
        fuel_update = make_callback_update(data="profile_set_fuel")
        context = make_context(user_data={"lang": "en"})

        lang_state = await profile.ask_language(lang_update, context)
        self.assertEqual(lang_state, STEP_PROFILE_LANGUAGE)
        markup = lang_update.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual(
            keyboard_layout(markup),
            [[("Italiano", "set_lang_it"), ("English", "set_lang_en")], [("↩", "profile")]],
        )

        fuel_state = await profile.ask_fuel(fuel_update, context)
        self.assertEqual(fuel_state, STEP_PROFILE_FUEL)
        markup = fuel_update.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual(
            keyboard_layout(markup),
            [[("Gasoline", "set_fuel_1"), ("Diesel", "set_fuel_2")], [("↩", "profile")]],
        )

    async def test_save_language_and_save_fuel_update_profile_and_return_to_menu(self):
        lang_update = make_callback_update(data="set_lang_en")
        fuel_update = make_callback_update(data="set_fuel_2")
        context = make_context(user_data={"lang": "it"})

        with (
            patch.object(profile, "_get_or_create_defaults", new=AsyncMock(return_value=("1", "it"))),
            patch.object(profile, "upsert_user", new=AsyncMock()) as upsert_user,
        ):
            lang_state = await profile.save_language(lang_update, context)

        self.assertEqual(lang_state, STEP_PROFILE_MENU)
        upsert_user.assert_awaited_once_with(1, "tester", "1", "en")
        self.assertEqual(context.user_data["lang"], "en")
        self.assertIn("Language updated successfully", lang_update.callback_query.edit_message_text.await_args.args[0])

        with (
            patch.object(profile, "_get_or_create_defaults", new=AsyncMock(return_value=("1", "en"))),
            patch.object(profile, "upsert_user", new=AsyncMock()) as upsert_user,
        ):
            fuel_state = await profile.save_fuel(fuel_update, context)

        self.assertEqual(fuel_state, STEP_PROFILE_MENU)
        upsert_user.assert_awaited_once_with(1, "tester", "2", "en")
        self.assertIn("Fuel updated successfully", fuel_update.callback_query.edit_message_text.await_args.args[0])

    async def test_back_to_menu_and_invalid_text_follow_current_state(self):
        update = make_callback_update(data="profile")
        context = make_context()

        with patch.object(profile, "_get_or_create_defaults", new=AsyncMock(return_value=("2", "en"))):
            state = await profile.back_to_menu(update, context)

        self.assertEqual(state, STEP_PROFILE_MENU)
        self.assertIn("Fuel", update.callback_query.edit_message_text.await_args.args[0])
        self.assertEqual(context.chat_data["current_state"], STEP_PROFILE_MENU)

        text_update = make_message_update(text="hello")
        menu_context = make_context(chat_data={"current_state": STEP_PROFILE_MENU})
        self.assertEqual(await profile.invalid_text(text_update, menu_context), ConversationHandler.END)

        with patch.object(profile, "ask_language", new=AsyncMock(return_value=STEP_PROFILE_LANGUAGE)) as ask_language:
            language_context = make_context(chat_data={"current_state": STEP_PROFILE_LANGUAGE})
            self.assertEqual(await profile.invalid_text(text_update, language_context), STEP_PROFILE_LANGUAGE)
        ask_language.assert_awaited_once_with(text_update, language_context)

        with patch.object(profile, "ask_fuel", new=AsyncMock(return_value=STEP_PROFILE_FUEL)) as ask_fuel:
            fuel_context = make_context(chat_data={"current_state": STEP_PROFILE_FUEL})
            self.assertEqual(await profile.invalid_text(text_update, fuel_context), STEP_PROFILE_FUEL)
        ask_fuel.assert_awaited_once_with(text_update, fuel_context)


if __name__ == "__main__":
    unittest.main()
