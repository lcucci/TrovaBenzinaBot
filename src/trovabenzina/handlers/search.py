"""
Fuel stations search conversation.

Supports searching by GPS location or typed address, with radius refinement
callbacks and a compact results layout.
"""

from typing import Optional

from telegram import Update, ReplyKeyboardRemove, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from ..api import get_station_address, search_stations, geocode_address_with_country
from ..config import GEOCODE_HARD_CAP
from ..db import (
    get_user,
    save_search,
    get_geocache,
    save_geocache,
    count_geocoding_month_calls,
    get_uom_by_code,
    get_user_language_code_by_tg_id,
    get_fuel_name_by_code,
)
from ..i18n import t
from ..utils import (
    STEP_SEARCH_LOCATION,
    format_price_unit,
    format_price,
    format_avg_comparison_text,
    format_date,
    format_directions_url,
    format_radius,
    inline_kb,
    reroute_command,
)

__all__ = ["search_ep", "search_handler", "radius_callback_handler"]

_CB_NARROW = "search:r=2.5"
_CB_WIDEN = "search:r=7.5"
_INITIAL_RADIUS = 5.0


def _message_from_update(update: Update):
    """
    Return the message object from Update (works for message or callback).
    """
    msg_obj = getattr(update, "message", None)
    if msg_obj is None and getattr(update, "callback_query", None):
        msg_obj = update.callback_query.message
    return msg_obj


async def _clear_processing_toast(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """
    Delete a previously sent 'processing' message if present.
    """
    proc_id = ctx.user_data.pop("processing_msg_id", None)
    if proc_id:
        try:
            await ctx.bot.delete_message(chat_id, proc_id)
        except Exception:
            # Safe to ignore if already gone
            pass


async def search_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for /search: ask for a location or address.

    Args:
        update: Telegram update.
        ctx: Callback context.

    Returns:
        int: Conversation state expecting a location or text address.
    """
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    return STEP_SEARCH_LOCATION


async def search_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive a GPS location and run the initial search at 5 km.

    Args:
        update: Telegram update with a location.
        ctx: Callback context.

    Returns:
        int: Conversation END (results will be posted immediately).
    """
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    proc_msg = await update.message.reply_text(
        t("processing_search", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    ctx.user_data["processing_msg_id"] = proc_msg.message_id

    loc = update.message.location
    ctx.user_data["search_lat"] = loc.latitude
    ctx.user_data["search_lng"] = loc.longitude

    ctx.user_data["radius_processing"] = False
    ctx.user_data["radius_clicked"] = set()

    await run_search(update, ctx, radius_km=_INITIAL_RADIUS, show_initial_cta=True)
    return ConversationHandler.END


async def search_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive a typed address, geocode it (with cache) and run the search.

    Args:
        update: Telegram update with text.
        ctx: Callback context.

    Returns:
        int: Conversation END (results will be posted immediately).
    """
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    proc_msg = await update.message.reply_text(
        t("processing_search", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    ctx.user_data["processing_msg_id"] = proc_msg.message_id

    address = update.message.text.strip()
    record = await get_geocache(address)
    if record:
        lat, lng = record.lat, record.lng
    else:
        stats = await count_geocoding_month_calls()
        if stats >= GEOCODE_HARD_CAP:
            await _clear_processing_toast(ctx, update.effective_chat.id)
            await update.message.reply_text(t("geocode_cap_reached", lang))
            return STEP_SEARCH_LOCATION

        # Country-aware geocoding
        coords = await geocode_address_with_country(address)
        if not coords:
            await _clear_processing_toast(ctx, update.effective_chat.id)
            await update.message.reply_text(t("invalid_address", lang))
            return STEP_SEARCH_LOCATION

        lat, lng, country = coords

        # If the address is not in Italy, inform the user and stop
        if country and country != "IT":
            await _clear_processing_toast(ctx, update.effective_chat.id)
            await update.message.reply_text(t("italy_only", lang))
            return STEP_SEARCH_LOCATION

        # Cache if not already cached (idempotent)
        await save_geocache(address, lat, lng)

    ctx.user_data["search_lat"] = lat
    ctx.user_data["search_lng"] = lng
    ctx.user_data["radius_processing"] = False
    ctx.user_data["radius_clicked"] = set()

    await run_search(update, ctx, radius_km=_INITIAL_RADIUS, show_initial_cta=True)
    return ConversationHandler.END


async def run_search(
        origin: Update,
        ctx: ContextTypes.DEFAULT_TYPE,
        *,
        radius_km: float,
        show_initial_cta: bool = False,
        followup_offer_radius: Optional[float] = None,
) -> None:
    """
    Execute one search and render results.

    Args:
        origin: The original update (message or callback).
        ctx: Callback context.
        radius_km: Search radius in kilometers.
        show_initial_cta: If True, attach both 2.5 and 7.5 buttons.
        followup_offer_radius: If set, attach only the remaining single button.
    """
    msg_obj = _message_from_update(origin)

    uid = origin.effective_user.id
    fuel_code, lang = await get_user(uid)
    lat = ctx.user_data.get("search_lat")
    lng = ctx.user_data.get("search_lng")
    if lat is None or lng is None:
        await msg_obj.reply_text(t("search_session_expired", lang))
        return

    # Fuel metadata
    uom = (await get_uom_by_code(fuel_code)) or "L"
    price_unit = format_price_unit(uom=uom, t=t, lang=lang)
    fuel_name = await get_fuel_name_by_code(fuel_code)

    fid = int(fuel_code)
    ft = f"{fuel_code}-x"

    res = await search_stations(lat, lng, radius_km, ft)

    # Clear "processing" toast if any
    await _clear_processing_toast(ctx, msg_obj.chat.id)

    if res is None:
        await msg_obj.reply_text(t("search_temporarily_unavailable", lang))
        await save_search(uid, fuel_code, radius_km, 0, None, None)
        return

    stations = res.get("results", [])
    num_stations = len(stations)

    # Filter by fuelId and select the price candidate per station
    filtered = []
    for st in stations:
        fuels = [f for f in st.get("fuels", []) if f.get("fuelId") == fid]
        if fuels:
            st["_filtered_fuels"] = fuels
            filtered.append(st)

    if not filtered:
        await msg_obj.reply_text(
            f"<u>{t('area_label', lang, radius=format_radius(radius_km))}</u> 📍\n\n{t('no_stations', lang)}",
            parse_mode=ParseMode.HTML,
        )
        await save_search(uid, fuel_code, radius_km, num_stations, None, None)
        return

    # Keep cheapest; tie-break preferring self-service
    all_fuels = [f for st in filtered for f in st["_filtered_fuels"]]
    min_fuel = min(all_fuels, key=lambda f: (f["price"], not f.get("isSelf")))
    target_is_self = min_fuel.get("isSelf")

    for st in filtered:
        st["_chosen_fuel"] = min(
            st["_filtered_fuels"], key=lambda f: (f["price"], not f.get("isSelf"))
        )
    filtered = [st for st in filtered if st["_chosen_fuel"].get("isSelf") == target_is_self]
    num_stations = len(filtered)

    if not filtered:
        await msg_obj.reply_text(
            f"<u>{t('area_label', lang, radius=format_radius(radius_km))}</u> 📍\n\n{t('no_stations', lang)}",
            parse_mode=ParseMode.HTML,
        )
        await save_search(uid, fuel_code, radius_km, num_stations, None, None)
        return

    avg = sum(st["_chosen_fuel"]["price"] for st in filtered) / len(filtered)
    below_avg = [st for st in filtered if st["_chosen_fuel"]["price"] <= avg]

    if not below_avg:
        await msg_obj.reply_text(
            f"<u>{t('area_label', lang, radius=format_radius(radius_km))}</u> 📍\n\n{t('no_stations', lang)}",
            parse_mode=ParseMode.HTML,
        )
        await save_search(uid, fuel_code, radius_km, num_stations, None, None)
        return

    sorted_res = sorted(below_avg, key=lambda r: r["_chosen_fuel"]["price"])
    lowest = sorted_res[0]["_chosen_fuel"]["price"]

    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, station in enumerate(sorted_res[:3]):
        f0 = station["_chosen_fuel"]
        price = f0["price"]
        dir_url = format_directions_url(
            station["location"]["lat"], station["location"]["lng"]
        )
        if not station.get("address"):
            station["address"] = await get_station_address(station["id"]) or t("no_address", lang)
        formatted_date = format_date(station.get("insertDate"), t=t, lang=lang)
        price_txt = format_price(price, price_unit)
        price_note = format_avg_comparison_text(price, avg, t=t, lang=lang)

        lines.append(
            f"{medals[i]} <b><a href=\"{dir_url}\">{station['brand']} • {station['name']}</a></b>\n"
            f"• <u>{t('address', lang)}</u>: {station['address']}\n"
            f"• <u>{t('price', lang)}</u>: <b>{price_txt}</b>, {price_note}\n"
            f"<i>[{t('last_update', lang)}: {formatted_date}]</i>"
        )

    header = (
        f"<b><u>{t('area_label', lang, radius=format_radius(radius_km))}</u></b> 📍\n"
        f"{num_stations} {t('stations_analyzed', lang)}\n"
        f"{t('average_zone_price', lang, fuel_name=t(fuel_name, lang))}: <b>{format_price(avg, price_unit)}</b>\n\n"
    )

    reply_markup = None
    if show_initial_cta:
        items = [
            (t("btn_narrow", lang, radius="2.5"), _CB_NARROW),
            (t("btn_widen", lang, radius="7.5"), _CB_WIDEN),
        ]
        reply_markup = InlineKeyboardMarkup(inline_kb(items, per_row=1))
    elif followup_offer_radius is not None:
        # Offer only the remaining radius on follow-up messages
        if abs(followup_offer_radius - 2.5) < 1e-6:
            items = [(t("btn_narrow", lang, radius="2.5"), _CB_NARROW)]
        else:
            items = [(t("btn_widen", lang, radius="7.5"), _CB_WIDEN)]
        reply_markup = InlineKeyboardMarkup(inline_kb(items, per_row=1))

    await msg_obj.reply_text(
        header + "\n\n".join(lines) + "\n\n\n" + t("disclaimer", lang),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=reply_markup,
    )

    await save_search(
        uid,
        fuel_code,
        radius_km,
        num_stations,
        round(avg, 3),
        round(lowest, 3),
    )


async def radius_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Refine radius to 2.5 km or 7.5 km with double-tap guard.

    UX rules:
      - guard against double taps
      - strip ALL buttons from the source message
      - show a temporary 'processing' toast
      - send new results with the remaining single button
    """
    query = update.callback_query
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)

    # Anti double tap
    if ctx.user_data.get("radius_processing"):
        await query.answer(t("please_wait", lang))
        return
    ctx.user_data["radius_processing"] = True

    try:
        await query.answer()
        data = (query.data or "").strip()

        # Track clicked radii in-session
        clicked = set(ctx.user_data.get("radius_clicked") or set())
        if data == _CB_NARROW:
            clicked.add("2.5")
        elif data == _CB_WIDEN:
            clicked.add("7.5")
        ctx.user_data["radius_clicked"] = clicked

        # 1) Remove ALL buttons from the source message
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass

        # 2) 'Processing' toast (removed by run_search)
        proc = await query.message.reply_text(
            t("processing_search", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        ctx.user_data["processing_msg_id"] = proc.message_id

        # 3) Compute remaining offer (if any) and run search
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
        STEP_SEARCH_LOCATION: [
            MessageHandler(filters.LOCATION, search_receive_location),
            MessageHandler(filters.TEXT & ~filters.COMMAND, search_receive_text),
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
