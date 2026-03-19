# ES - Español
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "es",
    "language_name": "Español",
    "gasoline": "Gasolina",
    "diesel": "Diésel",
    "cng": "GNC",
    "lpg": "GLP",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Selecciona idioma 🌐️",
    "invalid_language": "⚠️ ¡Idioma no válido!",
    "select_fuel": "Selecciona combustible ⛽",
    "invalid_fuel": "⚠️ ¡Combustible no válido!",
    "profile_saved": "✅ ¡Perfil guardado correctamente!\n\nUsa el comando /search para iniciar una búsqueda.",
    "user_already_registered": "⚠️ ¡Usuario ya registrado!\n\nUsa el comando /profile para cambiar las preferencias o el comando /search para iniciar una búsqueda.",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – inicia el bot y configura el perfil\n"
        "🔍 /search – busca las estaciones más económicas\n"
        "👤 /profile – ver y modificar tus ajustes\n"
        "📊 /statistics – ver tus estadísticas\n"
        "📢 /help – mostrar este mensaje\n\n"
    ),
    "disclaimer": (
        "ℹ️ Datos de las estaciones proporcionados por el <b>Ministerio de Empresas y Made in Italy (MISE)</b>.\n"
        "No se garantiza la exactitud ni la actualización de la información mostrada por el bot."
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Idioma",
    "fuel": "⛽ Combustible",
    "edit_language": "Editar idioma 🌐️",
    "edit_fuel": "Editar combustible ⛽",
    "language_updated": "✅ ¡Idioma actualizado correctamente!",
    "fuel_updated": "✅ ¡Combustible actualizado correctamente!",

    # ─────────── /search ───────────
    "ask_location": "Escribe una dirección o envía tu ubicación 📍",
    "send_location": "Enviar ubicación GPS 🌍",
    "geocode_cap_reached": "⚠️ ¡El reconocimiento de direcciones no está disponible por el momento!\n\nVuelve a intentarlo más tarde, o envía tu ubicación.",
    "invalid_address": "⚠️ ¡Dirección no válida!\n\nIntroduce otra dirección o envía tu ubicación.",
    "italy_only": "⚠️ La búsqueda solo está disponible en Italia!\n\nEscribe una dirección en Italia o envía tu ubicación.",
    "processing_search": "Búsqueda en curso.🔍",
    "please_wait": "Operación en curso, espera un momento.⏳",
    "search_temporarily_unavailable": "⚠️ ¡Servicio temporalmente no disponible!\n\nPor favor, inténtalo de nuevo más tarde.",
    "no_stations": "❌ No se han encontrado estaciones",
    "area_label": "Estaciones en un radio de {radius} km",
    "stations_analyzed": "estaciones analizadas",
    "average_zone_price": "Precio medio de {fuel_name} en la zona",
    "address": "Dirección",
    "no_address": "-",
    "price": "Precio",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "más económico que la media",
    "equal_average": "en línea con la media",
    "last_update": "Última actualización",
    "btn_narrow": "Repetir búsqueda con un radio de {radius} km 🔄",
    "btn_widen": "Repetir búsqueda con un radio de {radius} km 🔄",
    "search_session_expired": "⚠️ ¡Sesión caducada!\n\nUsa el comando /search para iniciar una nueva búsqueda.",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ ¡No hay estadísticas disponibles!\n\nUsa el comando /search para iniciar una búsqueda.",
    "statistics": (
        "<b><u>Estadísticas {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} búsquedas</b> realizadas.\n"
        "<b>{num_stations} estaciones</b> analizadas.\n"
        "Ahorro medio: <b>{avg_eur_save_per_unit} {price_unit}</b>, es decir, <b>{avg_pct_save}%</b>.\n"
        "Ahorro anual estimado: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>❓ ¿Cómo hemos calculado estos datos?</i>\n"
                       "• El ahorro medio se calcula como la media del ahorro obtenido en cada búsqueda, igual a la diferencia entre el precio medio de la zona y el precio de la estación más barata encontrada.\n"
                       "• El ahorro anual se calcula suponiendo un recorrido de 10.000 km al año con un consumo medio de: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} cada 100 km",
    "reset_statistics": "Restablecer estadísticas ♻️",
    "statistics_reset": "✅ ¡Estadísticas restablecidas correctamente!\n\nUsa el comando /search para iniciar una búsqueda.",

    "unknown_command_hint": "⚠️ ¡Comando no válido!\n\nUsa el comando /help para ver la lista de comandos disponibles.",

}
