# RU - Русский
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "ru",
    "language_name": "Русский",
    "gasoline": "Бензин",
    "diesel": "Дизель",
    "cng": "сжатый природный газ",
    "lpg": "сжиженный нефтяной газ",
    "liter_symbol": "L",
    "kilo_symbol": "кг",

    # ─────────── /start ───────────
    "select_language": "Выберите язык 🌐️",
    "invalid_language": "⚠️ Недопустимый язык!",
    "select_fuel": "Выберите топливо ⛽",
    "invalid_fuel": "⚠️ Недопустимое топливо!",
    "profile_saved": "✅ Профиль успешно сохранён!\n\nИспользуйте команду /search, чтобы начать поиск.",
    "user_already_registered": "⚠️ Пользователь уже зарегистрирован!\n\nИспользуйте /profile, чтобы изменить настройки, или /search, чтобы начать поиск.",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – запустить бота и настроить профиль\n"
        "🔍 /search – найти самые дешёвые заправки\n"
        "👤 /profile – просмотреть и изменить настройки\n"
        "📊 /statistics – посмотреть статистику\n"
        "📢 /help – показать это сообщение\n\n"
    ),
    "disclaimer": (
        "ℹ️ Данные по заправкам предоставлены <b>Министерством предприятий и Made in Italy (MISE)</b>.\n"
        "Точность и актуальность информации, отображаемой ботом, не гарантируются."
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Язык",
    "fuel": "⛽ Топливо",
    "edit_language": "Изменить язык 🌐️",
    "edit_fuel": "Изменить топливо ⛽",
    "language_updated": "✅ Язык успешно обновлён!",
    "fuel_updated": "✅ Топливо успешно обновлено!",

    # ─────────── /search ───────────
    "choose_search_mode": "Vyberite tip poiska.",
    "btn_search_zone": "Ryadom s tochkoy 📌",
    "btn_search_route": "Po marshrutu 🛣️",
    "ask_location": "Введите адрес или отправьте свою геопозицию 📍",
    "ask_route_origin": "Vvedite adres otpravleniya.",
    "ask_route_destination": "Vvedite adres pribytiya.",
    "send_location": "Отправить геопозицию (GPS) 🌍",
    "geocode_cap_reached": "⚠️ Распознавание адресов временно недоступно!\n\nПовторите попытку позже или отправьте свою геопозицию.",
    "invalid_address": "⚠️ Недопустимый адрес!\n\nВведите другой адрес или отправьте свою геопозицию.",
    "italy_only": "⚠️ Поиск доступен только в Италии!\n\nВведите итальянский адрес или отправьте свою геопозицию.",
    "processing_search": "Выполняется поиск.🔍",
    "please_wait": "Выполняется операция, подождите немного.⏳",
    "search_temporarily_unavailable": "⚠️ Сервис временно недоступен!\n\nПожалуйста, попробуйте позже.",
    "no_stations": "❌ Заправки не найдены",
    "area_label": "Заправки в радиусе {radius} км",
    "stations_analyzed": "станций проанализировано",
    "average_zone_price": "Средняя цена {fuel_name} в зоне",
    "route_label": "Zapravki po marshrutu",
    "average_route_price": "Srednyaya tsena {fuel_name} po marshrutu",
    "address": "Адрес",
    "no_address": "-",
    "price": "Цена",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "дешевле среднего",
    "equal_average": "соответствует среднему",
    "last_update": "Последнее обновление",
    "btn_narrow": "Повторить поиск с радиусом {radius} км 🔄",
    "btn_widen": "Повторить поиск с радиусом {radius} км 🔄",
    "search_session_expired": "⚠️ Сессия истекла!\n\nИспользуйте /search, чтобы начать новый поиск.",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ Статистика недоступна!\n\nИспользуйте /search для начала поиска.",
    "statistics": (
        "<b><u>Статистика {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} запросов</b> выполнено.\n"
        "<b>{num_stations} станций</b> проанализировано.\n"
        "Средняя экономия: <b>{avg_eur_save_per_unit} {price_unit}</b>, что составляет <b>{avg_pct_save}%</b>.\n"
        "Оценочная годовая экономия: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>❓ Как мы рассчитали эти показатели?</i>\n"
                       "• Средняя экономия — это средняя по всем поискам разница между средним ценником по зоне и самой дешёвой найденной заправкой.\n"
                       "• Годовая экономия предполагает пробег 10 000 км в год со средним расходом: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} на 100 км",
    "reset_statistics": "Сбросить статистику ♻️",
    "statistics_reset": "✅ Статистика успешно сброшена!\n\nИспользуйте /search для начала поиска.",

    "unknown_command_hint": "⚠️ Недопустимая команда!\n\nИспользуйте команду /help, чтобы просмотреть список доступных команд.",

}
