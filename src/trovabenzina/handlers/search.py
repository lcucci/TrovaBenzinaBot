"""Fuel stations search conversation."""

from typing import Any, Optional

from telegram import InlineKeyboardMarkup, Message, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..api import (
    geocode_address_with_country,
    get_station_address,
    search_route_stations,
    search_stations,
)
from ..config import GEOCODE_HARD_CAP
from ..db import (
    count_geocoding_month_calls,
    get_fuel_name_by_code,
    get_geocache,
    get_uom_by_code,
    get_user,
    get_user_language_code_by_tg_id,
    save_geocache,
    save_search,
)
from ..i18n import t
from ..utils import (
    STEP_SEARCH_LOCATION,
    STEP_SEARCH_MODE,
    STEP_SEARCH_ROUTE_DESTINATION,
    STEP_SEARCH_ROUTE_ORIGIN,
    format_avg_comparison_text,
    format_date,
    format_directions_url,
    format_price,
    format_price_unit,
    format_radius,
    inline_kb,
    reroute_command,
)

__all__ = ["search_ep", "search_handler", "radius_callback_handler"]

_CB_MODE_ZONE = "search:mode:zone"
_CB_MODE_ROUTE = "search:mode:route"
_CB_NARROW = "search:r=2.5"
_CB_WIDEN = "search:r=7.5"
_INITIAL_RADIUS = 5.0


def _message_from_update(update: Update) -> Message:
    """Return the Telegram message bound to the update."""
    msg_obj = getattr(update, "message", None)
    if msg_obj is None and getattr(update, "callback_query", None):
        msg_obj = update.callback_query.message
    return msg_obj


async def _clear_processing_toast(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Delete a previously sent processing message if present."""
    proc_id = ctx.user_data.pop("processing_msg_id", None)
    if proc_id:
        try:
            await ctx.bot.delete_message(chat_id, proc_id)
        except Exception:
            pass


async def _show_processing_toast(
        message: Message,
        ctx: ContextTypes.DEFAULT_TYPE,
        lang: str,
) -> None:
    """Send and remember a temporary processing message."""
    proc_msg = await message.reply_text(
        t("processing_search", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    ctx.user_data["processing_msg_id"] = proc_msg.message_id


async def _delete_message_safely(
        ctx: ContextTypes.DEFAULT_TYPE,
        *,
        chat_id: int,
        message_id: int,
) -> None:
    """Delete a bot message, ignoring races and already-deleted messages."""
    try:
        await ctx.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


def _reset_search_session(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Drop all temporary search state before starting a new flow."""
    for key in (
            "processing_msg_id",
            "search_mode",
            "search_lat",
            "search_lng",
            "radius_processing",
            "radius_clicked",
            "route_origin_lat",
            "route_origin_lng",
            "route_destination_lat",
            "route_destination_lng",
    ):
        ctx.user_data.pop(key, None)


def _build_search_mode_markup(lang: str) -> InlineKeyboardMarkup:
    """Return the inline keyboard used to choose the search mode."""
    items = [
        (t("btn_search_zone", lang), _CB_MODE_ZONE),
        (t("btn_search_route", lang), _CB_MODE_ROUTE),
    ]
    return InlineKeyboardMarkup(inline_kb(items, per_row=1))


async def _resolve_address_to_coords(
        address: str,
) -> tuple[Optional[tuple[float, float]], Optional[str]]:
    """Resolve an address through geocache and Google geocoding."""
    record = await get_geocache(address)
    if record:
        return (record.lat, record.lng), None

    stats = await count_geocoding_month_calls()
    if stats >= GEOCODE_HARD_CAP:
        return None, "geocode_cap_reached"

    coords = await geocode_address_with_country(address)
    if not coords:
        return None, "invalid_address"

    lat, lng, country = coords
    if country and country != "IT":
        return None, "italy_only"

    await save_geocache(address, lat, lng)
    return (lat, lng), None


def _select_station_results(
        stations: list[dict[str, Any]],
        fuel_id: int,
) -> tuple[list[dict[str, Any]], int, Optional[float], Optional[float]]:
    """Apply the shared fuel and service ranking logic to MISE results."""
    num_stations = len(stations)
    filtered = []
    for station in stations:
        fuels = [fuel for fuel in station.get("fuels", []) if fuel.get("fuelId") == fuel_id]
        if fuels:
            station["_filtered_fuels"] = fuels
            filtered.append(station)

    if not filtered:
        return [], num_stations, None, None

    all_fuels = [fuel for station in filtered for fuel in station["_filtered_fuels"]]
    min_fuel = min(all_fuels, key=lambda fuel: (fuel["price"], not fuel.get("isSelf")))
    target_is_self = min_fuel.get("isSelf")

    for station in filtered:
        station["_chosen_fuel"] = min(
            station["_filtered_fuels"],
            key=lambda fuel: (fuel["price"], not fuel.get("isSelf")),
        )

    filtered = [station for station in filtered if station["_chosen_fuel"].get("isSelf") == target_is_self]
    num_stations = len(filtered)
    if not filtered:
        return [], num_stations, None, None

    avg = sum(station["_chosen_fuel"]["price"] for station in filtered) / len(filtered)
    below_avg = [station for station in filtered if station["_chosen_fuel"]["price"] <= avg]
    if not below_avg:
        return [], num_stations, None, None

    sorted_results = sorted(below_avg, key=lambda station: station["_chosen_fuel"]["price"])
    lowest = sorted_results[0]["_chosen_fuel"]["price"]
    return sorted_results, num_stations, avg, lowest


async def _build_results_lines(
        stations: list[dict[str, Any]],
        *,
        lang: str,
        avg_price: float,
        price_unit: str,
) -> list[str]:
    """Format the top three stations into localized HTML blocks."""
    medals = ["\U0001F947", "\U0001F948", "\U0001F949"]
    lines = []
    for i, station in enumerate(stations[:3]):
        chosen_fuel = station["_chosen_fuel"]
        price = chosen_fuel["price"]
        dir_url = format_directions_url(station["location"]["lat"], station["location"]["lng"])
        if not station.get("address"):
            station["address"] = await get_station_address(station["id"]) or t("no_address", lang)
        formatted_date = format_date(station.get("insertDate"), t=t, lang=lang)
        price_txt = format_price(price, price_unit)
        price_note = format_avg_comparison_text(price, avg_price, t=t, lang=lang)

        lines.append(
            f"{medals[i]} <b><a href=\"{dir_url}\">{station['brand']} - {station['name']}</a></b>\n"
            f"• <u>{t('address', lang)}</u>: {station['address']}\n"
            f"• <u>{t('price', lang)}</u>: <b>{price_txt}</b>, {price_note}\n"
            f"<i>[{t('last_update', lang)}: {formatted_date}]</i>"
        )

    return lines


async def _reply_no_stations(
        msg_obj: Message,
        *,
        lang: str,
        title: str,
) -> None:
    """Reply with a localized empty-results message."""
    await msg_obj.reply_text(
        f"<u>{title}</u>\n\n{t('no_stations', lang)}",
        parse_mode=ParseMode.HTML,
    )


async def _render_search_results(
        msg_obj: Message,
        *,
        lang: str,
        title: str,
        average_label: str,
        sorted_results: list[dict[str, Any]],
        num_stations: int,
        avg_price: float,
        price_unit: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """Render a successful search response."""
    lines = await _build_results_lines(
        sorted_results,
        lang=lang,
        avg_price=avg_price,
        price_unit=price_unit,
    )

    header = (
        f"<b><u>{title}</u></b>\n"
        f"{num_stations} {t('stations_analyzed', lang)}\n"
        f"{average_label}: <b>{format_price(avg_price, price_unit)}</b>\n\n"
    )

    await msg_obj.reply_text(
        header + "\n\n".join(lines) + "\n\n\n" + t("disclaimer", lang),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=reply_markup,
    )


async def search_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /search: ask which search mode to use."""
    _reset_search_session(ctx)
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await update.effective_message.reply_text(
        t("choose_search_mode", lang),
        reply_markup=_build_search_mode_markup(lang),
    )
    return STEP_SEARCH_MODE


async def repeat_search_mode_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Repeat the search mode prompt when the user sends a regular message."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await update.effective_message.reply_text(
        t("choose_search_mode", lang),
        reply_markup=_build_search_mode_markup(lang),
    )
    return STEP_SEARCH_MODE


async def search_mode_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the zone vs route selection."""
    query = update.callback_query
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await query.answer()

    await _delete_message_safely(
        ctx,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )

    if query.data == _CB_MODE_ZONE:
        ctx.user_data["search_mode"] = "zone"
        await ctx.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t("ask_location", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        return STEP_SEARCH_LOCATION

    ctx.user_data["search_mode"] = "route"
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t("ask_route_origin", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    return STEP_SEARCH_ROUTE_ORIGIN


async def search_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive a GPS location and run the initial zone search at 5 km."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await _show_processing_toast(update.message, ctx, lang)

    loc = update.message.location
    ctx.user_data["search_mode"] = "zone"
    ctx.user_data["search_lat"] = loc.latitude
    ctx.user_data["search_lng"] = loc.longitude
    ctx.user_data["radius_processing"] = False
    ctx.user_data["radius_clicked"] = set()

    await run_search(update, ctx, radius_km=_INITIAL_RADIUS, show_initial_cta=True)
    return ConversationHandler.END


async def search_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive a typed address, geocode it and run the zone search."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await _show_processing_toast(update.message, ctx, lang)

    address = (update.message.text or "").strip()
    coords, error_key = await _resolve_address_to_coords(address)
    if error_key:
        await _clear_processing_toast(ctx, update.effective_chat.id)
        await update.message.reply_text(t(error_key, lang))
        return STEP_SEARCH_LOCATION

    lat, lng = coords
    ctx.user_data["search_mode"] = "zone"
    ctx.user_data["search_lat"] = lat
    ctx.user_data["search_lng"] = lng
    ctx.user_data["radius_processing"] = False
    ctx.user_data["radius_clicked"] = set()

    await run_search(update, ctx, radius_km=_INITIAL_RADIUS, show_initial_cta=True)
    return ConversationHandler.END


async def search_receive_route_origin(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and geocode the route origin address."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    if not update.message.text:
        await update.message.reply_text(
            t("ask_route_origin", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        return STEP_SEARCH_ROUTE_ORIGIN

    await _show_processing_toast(update.message, ctx, lang)
    address = update.message.text.strip()
    coords, error_key = await _resolve_address_to_coords(address)
    if error_key:
        await _clear_processing_toast(ctx, update.effective_chat.id)
        await update.message.reply_text(t(error_key, lang))
        await update.message.reply_text(
            t("ask_route_origin", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        return STEP_SEARCH_ROUTE_ORIGIN

    origin_lat, origin_lng = coords
    ctx.user_data["search_mode"] = "route"
    ctx.user_data["route_origin_lat"] = origin_lat
    ctx.user_data["route_origin_lng"] = origin_lng

    await _clear_processing_toast(ctx, update.effective_chat.id)
    await update.message.reply_text(
        t("ask_route_destination", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    return STEP_SEARCH_ROUTE_DESTINATION


async def search_receive_route_destination(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and geocode the route destination, then run the route search."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    if not update.message.text:
        await update.message.reply_text(
            t("ask_route_destination", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        return STEP_SEARCH_ROUTE_DESTINATION

    await _show_processing_toast(update.message, ctx, lang)
    address = update.message.text.strip()
    coords, error_key = await _resolve_address_to_coords(address)
    if error_key:
        await _clear_processing_toast(ctx, update.effective_chat.id)
        await update.message.reply_text(t(error_key, lang))
        await update.message.reply_text(
            t("ask_route_destination", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        return STEP_SEARCH_ROUTE_DESTINATION

    destination_lat, destination_lng = coords
    ctx.user_data["search_mode"] = "route"
    ctx.user_data["route_destination_lat"] = destination_lat
    ctx.user_data["route_destination_lng"] = destination_lng

    await run_route_search(update, ctx)
    return ConversationHandler.END


async def run_search(
        origin: Update,
        ctx: ContextTypes.DEFAULT_TYPE,
        *,
        radius_km: float,
        show_initial_cta: bool = False,
        followup_offer_radius: Optional[float] = None,
) -> None:
    """Execute one zone search and render results."""
    msg_obj = _message_from_update(origin)

    uid = origin.effective_user.id
    fuel_code, lang = await get_user(uid)
    lat = ctx.user_data.get("search_lat")
    lng = ctx.user_data.get("search_lng")
    if lat is None or lng is None:
        await _clear_processing_toast(ctx, msg_obj.chat.id)
        await msg_obj.reply_text(t("search_session_expired", lang))
        return

    uom = (await get_uom_by_code(fuel_code)) or "L"
    price_unit = format_price_unit(uom=uom, t=t, lang=lang)
    fuel_name = await get_fuel_name_by_code(fuel_code)

    fid = int(fuel_code)
    fuel_type = f"{fuel_code}-x"
    res = await search_stations(lat, lng, radius_km, fuel_type)

    await _clear_processing_toast(ctx, msg_obj.chat.id)

    if res is None:
        await msg_obj.reply_text(t("search_temporarily_unavailable", lang))
        await save_search(uid, fuel_code, radius_km, 0, None, None, search_type="zone")
        return

    stations = res.get("results", [])
    sorted_results, num_stations, avg_price, lowest_price = _select_station_results(stations, fid)
    title = t("area_label", lang, radius=format_radius(radius_km))
    if not sorted_results:
        await _reply_no_stations(msg_obj, lang=lang, title=title)
        await save_search(uid, fuel_code, radius_km, num_stations, None, None, search_type="zone")
        return

    reply_markup = None
    if show_initial_cta:
        items = [
            (t("btn_narrow", lang, radius="2.5"), _CB_NARROW),
            (t("btn_widen", lang, radius="7.5"), _CB_WIDEN),
        ]
        reply_markup = InlineKeyboardMarkup(inline_kb(items, per_row=1))
    elif followup_offer_radius is not None:
        if abs(followup_offer_radius - 2.5) < 1e-6:
            items = [(t("btn_narrow", lang, radius="2.5"), _CB_NARROW)]
        else:
            items = [(t("btn_widen", lang, radius="7.5"), _CB_WIDEN)]
        reply_markup = InlineKeyboardMarkup(inline_kb(items, per_row=1))

    await _render_search_results(
        msg_obj,
        lang=lang,
        title=title,
        average_label=t("average_zone_price", lang, fuel_name=t(fuel_name, lang)),
        sorted_results=sorted_results,
        num_stations=num_stations,
        avg_price=avg_price,
        price_unit=price_unit,
        reply_markup=reply_markup,
    )

    await save_search(
        uid,
        fuel_code,
        radius_km,
        num_stations,
        round(avg_price, 3),
        round(lowest_price, 3),
        search_type="zone",
    )


async def run_route_search(origin: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute a route search and render results."""
    msg_obj = _message_from_update(origin)

    uid = origin.effective_user.id
    fuel_code, lang = await get_user(uid)
    origin_lat = ctx.user_data.get("route_origin_lat")
    origin_lng = ctx.user_data.get("route_origin_lng")
    destination_lat = ctx.user_data.get("route_destination_lat")
    destination_lng = ctx.user_data.get("route_destination_lng")
    if None in (origin_lat, origin_lng, destination_lat, destination_lng):
        await _clear_processing_toast(ctx, msg_obj.chat.id)
        await msg_obj.reply_text(t("search_session_expired", lang))
        return

    uom = (await get_uom_by_code(fuel_code)) or "L"
    price_unit = format_price_unit(uom=uom, t=t, lang=lang)
    fuel_name = await get_fuel_name_by_code(fuel_code)

    fid = int(fuel_code)
    fuel_type = f"{fuel_code}-x"
    res = await search_route_stations(origin_lat, origin_lng, destination_lat, destination_lng, fuel_type)

    await _clear_processing_toast(ctx, msg_obj.chat.id)

    if res is None:
        await msg_obj.reply_text(t("search_temporarily_unavailable", lang))
        await save_search(uid, fuel_code, None, 0, None, None, search_type="route")
        return

    stations = res.get("results", [])
    sorted_results, num_stations, avg_price, lowest_price = _select_station_results(stations, fid)
    title = t("route_label", lang)
    if not sorted_results:
        await _reply_no_stations(msg_obj, lang=lang, title=title)
        await save_search(uid, fuel_code, None, num_stations, None, None, search_type="route")
        return

    await _render_search_results(
        msg_obj,
        lang=lang,
        title=title,
        average_label=t("average_route_price", lang, fuel_name=t(fuel_name, lang)),
        sorted_results=sorted_results,
        num_stations=num_stations,
        avg_price=avg_price,
        price_unit=price_unit,
    )

    await save_search(
        uid,
        fuel_code,
        None,
        num_stations,
        round(avg_price, 3),
        round(lowest_price, 3),
        search_type="route",
    )


async def radius_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Refine a zone search to 2.5 km or 7.5 km with a double-tap guard."""
    query = update.callback_query
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)

    if ctx.user_data.get("radius_processing"):
        await query.answer(t("please_wait", lang))
        return
    ctx.user_data["radius_processing"] = True

    try:
        await query.answer()
        data = (query.data or "").strip()

        clicked = set(ctx.user_data.get("radius_clicked") or set())
        if data == _CB_NARROW:
            clicked.add("2.5")
        elif data == _CB_WIDEN:
            clicked.add("7.5")
        ctx.user_data["radius_clicked"] = clicked

        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass

        await _show_processing_toast(query.message, ctx, lang)

        remaining = {"2.5", "7.5"} - clicked
        if data == _CB_NARROW:
            offer = 7.5 if "7.5" in remaining else None
            await run_search(update, ctx, radius_km=2.5, followup_offer_radius=offer)
        elif data == _CB_WIDEN:
            offer = 2.5 if "2.5" in remaining else None
            await run_search(update, ctx, radius_km=7.5, followup_offer_radius=offer)
    finally:
        ctx.user_data["radius_processing"] = False


search_handler = ConversationHandler(
    entry_points=[CommandHandler("search", search_ep)],
    states={
        STEP_SEARCH_MODE: [
            CallbackQueryHandler(search_mode_callback, pattern=r"^search:mode:(?:zone|route)$"),
            MessageHandler(filters.ALL & ~filters.COMMAND, repeat_search_mode_prompt),
        ],
        STEP_SEARCH_LOCATION: [
            MessageHandler(filters.LOCATION, search_receive_location),
            MessageHandler(filters.TEXT & ~filters.COMMAND, search_receive_text),
        ],
        STEP_SEARCH_ROUTE_ORIGIN: [
            MessageHandler(filters.ALL & ~filters.COMMAND, search_receive_route_origin),
        ],
        STEP_SEARCH_ROUTE_DESTINATION: [
            MessageHandler(filters.ALL & ~filters.COMMAND, search_receive_route_destination),
        ],
    },
    fallbacks=[
        MessageHandler(filters.COMMAND, reroute_command),
    ],
    block=True,
    allow_reentry=True,
)

radius_callback_handler = CallbackQueryHandler(
    radius_callback, pattern=r"^search:r=(?:2\.5|7\.5)$"
)
