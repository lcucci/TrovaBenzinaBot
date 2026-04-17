# DE - Deutsch
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "de",
    "language_name": "Deutsch",
    "gasoline": "Benzin",
    "diesel": "Diesel",
    "cng": "Erdgas",
    "lpg": "Autogas",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Sprache auswählen 🌐️",
    "invalid_language": "⚠️ Ungültige Sprache!",
    "select_fuel": "Kraftstoff auswählen ⛽",
    "invalid_fuel": "⚠️ Ungültiger Kraftstoff!",
    "profile_saved": "✅ Profil erfolgreich gespeichert!\n\nVerwende den Befehl /search, um eine Suche zu starten.",
    "user_already_registered": "⚠️ Benutzer bereits registriert!\n\nVerwende den Befehl /profile, um die Einstellungen zu ändern, oder /search, um eine Suche zu starten.",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – Bot starten und Profil einrichten\n"
        "🔍 /search – günstigste Tankstellen finden\n"
        "👤 /profile – Einstellungen anzeigen und bearbeiten\n"
        "📊 /statistics – Statistiken anzeigen\n"
        "📢 /help – diese Nachricht anzeigen\n\n"
    ),
    "disclaimer": (
        "ℹ️ Daten zu Tankstellen werden vom <b>Ministerium für Unternehmen und Made in Italy (MISE)</b> bereitgestellt.\n"
        "Für die Genauigkeit oder Aktualität der vom Bot angezeigten Informationen wird keine Gewähr übernommen."
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Sprache",
    "fuel": "⛽ Kraftstoff",
    "edit_language": "Sprache ändern 🌐️",
    "edit_fuel": "Kraftstoff ändern ⛽",
    "language_updated": "✅ Sprache erfolgreich aktualisiert!",
    "fuel_updated": "✅ Kraftstoff erfolgreich aktualisiert!",

    # ─────────── /search ───────────
    "choose_search_mode": "Wahle die Art der Suche.",
    "btn_search_zone": "In der Nahe eines Punkts 📌",
    "btn_search_route": "Entlang einer Route 🛣️",
    "ask_location": "Gib eine Adresse ein oder sende deinen Standort 📍",
    "ask_route_origin": "Gib die Startadresse ein.",
    "ask_route_destination": "Gib die Zieladresse ein.",
    "send_location": "GPS-Standort senden 🌍",
    "geocode_cap_reached": "⚠️ Adresserkennung derzeit nicht verfügbar!\n\nBitte versuche es später erneut, oder sende deinen Standort.",
    "invalid_address": "⚠️ Ungültige Adresse!\n\nGib eine andere Adresse ein oder sende deinen Standort.",
    "italy_only": "⚠️ Die Suche ist nur in Italien verfügbar!\n\nGib eine italienische Adresse ein oder sende deinen Standort.",
    "processing_search": "Suche läuft.🔍",
    "please_wait": "Vorgang läuft, bitte einen Moment warten.⏳",
    "search_temporarily_unavailable": "⚠️ Dienst vorübergehend nicht verfügbar!\n\nBitte versuche es später erneut.",
    "no_stations": "❌ Keine Tankstellen gefunden",
    "area_label": "Tankstellen im Umkreis von {radius} km",
    "stations_analyzed": "Tankstellen analysiert",
    "average_zone_price": "Durchschnittspreis {fuel_name} in der Umgebung",
    "route_label": "Tankstellen entlang der Route",
    "average_route_price": "Durchschnittspreis {fuel_name} entlang der Route",
    "address": "Adresse",
    "no_address": "-",
    "price": "Preis",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "günstiger als der Durchschnitt",
    "equal_average": "entspricht dem Durchschnitt",
    "last_update": "Letzte Aktualisierung",
    "btn_narrow": "Suche mit Radius von {radius} km wiederholen 🔄",
    "btn_widen": "Suche mit Radius von {radius} km wiederholen 🔄",
    "search_session_expired": "⚠️ Sitzung abgelaufen!\n\nVerwende /search, um eine neue Suche zu starten.",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ Keine Statistiken verfügbar!\n\nVerwende /search, um eine Suche zu starten.",
    "statistics": (
        "<b><u>{fuel_name}-Statistiken</u></b> 📊\n"
        "<b>{num_searches} Suchen</b> durchgeführt.\n"
        "<b>{num_stations} Tankstellen</b> analysiert.\n"
        "Durchschnittliche Ersparnis: <b>{avg_eur_save_per_unit} {price_unit}</b>, also <b>{avg_pct_save}%</b>.\n"
        "Geschätzte jährliche Ersparnis: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>❓ Wie haben wir diese Werte berechnet?</i>\n"
                       "• Die durchschnittliche Ersparnis ist der Mittelwert über alle Suchen der Differenz zwischen dem Durchschnittspreis der Umgebung und dem vom Bot gefundenen günstigsten Preis.\n"
                       "• Die jährliche Ersparnis setzt 10.000km pro Jahr mit einem durchschnittlichen Verbrauch von: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} je 100km",
    "reset_statistics": "Statistiken zurücksetzen ♻️",
    "statistics_reset": "✅ Statistiken erfolgreich zurückgesetzt!\n\nVerwende /search, um eine Suche zu starten.",

    "unknown_command_hint": "⚠️ Ungültiger Befehl!\n\nVerwende den Befehl /help für eine Liste der verfügbaren Befehle.",

}
