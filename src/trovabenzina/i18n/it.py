# IT - Italiano
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "it",
    "language_name": "Italiano",
    "gasoline": "Benzina",
    "diesel": "Gasolio",
    "cng": "Metano",
    "lpg": "GPL",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Seleziona lingua 🌐️",
    "invalid_language": "⚠️ Lingua non valida!",
    "select_fuel": "Seleziona carburante ⛽",
    "invalid_fuel": "⚠️ Carburante non valido!",
    "profile_saved": "✅ Profilo salvato correttamente!\n\nUtilizza il comando /search per avviare una ricerca.",
    "user_already_registered": "⚠️ Utente già registrato!\n\nUtilizza il comando /profile per modificare le preferenze o il comando /search per avviare una ricerca.",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – avvia il bot e configura il profilo\n"
        "🔍 /search – cerca i distributori più economici\n"
        "👤 /profile – visualizza e modifica le tue impostazioni\n"
        "📊 /statistics – visualizza le tue statistiche\n"
        "📢 /help – mostra questo messaggio\n\n"
    ),
    "disclaimer": (
        "ℹ️ Dati sui distributori forniti dal <b>Ministero delle Imprese e del Made in Italy (MISE)</b>.\n"
        "Non si garantisce l'accuratezza o l'aggiornamento delle informazioni mostrate dal bot."
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Lingua",
    "fuel": "⛽ Carburante",
    "edit_language": "Modifica lingua 🌐️",
    "edit_fuel": "Modifica carburante ⛽",
    "language_updated": "✅ Lingua aggiornata correttamente!",
    "fuel_updated": "✅ Carburante aggiornato correttamente!",

    # ─────────── /search ───────────
    "choose_search_mode": "Scegli il tipo di ricerca da effettuare.",
    "btn_search_zone": "Vicino a un punto 📌",
    "btn_search_route": "Lungo un percorso 🛣️",
    "ask_location": "Digita un indirizzo oppure invia la tua posizione 📍",
    "ask_route_origin": "Digita l'indirizzo di partenza oppure invia la tua posizione 📍",
    "ask_route_destination": "Digita l'indirizzo di arrivo oppure invia la tua posizione 📍",
    "send_location": "Invia posizione GPS 🌍",
    "geocode_cap_reached": "⚠️ Riconoscimento indirizzo al momento non disponibile!\n\nPer favore riprova più tardi, oppure invia la tua posizione.",
    "invalid_address": "⚠️ Indirizzo non valido!\n\nDigita un altro indirizzo oppure invia la tua posizione.",
    "italy_only": "⚠️ La ricerca è disponibile solo in Italia!\n\nDigita un indirizzo italiano oppure invia la tua posizione.",
    "processing_search": "Ricerca in corso...🔍",
    "please_wait": "Operazione in corso, attendi un attimo...⏳",
    "search_temporarily_unavailable": "⚠️ Servizio momentaneamente non disponibile!\n\nPer favore riprova più tardi.",
    "no_stations": "❌ Nessun distributore trovato",
    "area_label": "Distributori nel raggio di {radius} km",
    "stations_analyzed": "stazioni analizzate",
    "average_zone_price": "Prezzo medio {fuel_name} nella zona",
    "route_label": "Distributori lungo il percorso",
    "average_route_price": "Prezzo medio {fuel_name} lungo il percorso",
    "address": "Indirizzo",
    "no_address": "-",
    "price": "Prezzo",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "più economico della media",
    "equal_average": "in linea con la media",
    "last_update": "Ultimo aggiornamento",
    "btn_narrow": "Ripetere ricerca con raggio di {radius} km 🔄",
    "btn_widen": "Ripetere ricerca con raggio di {radius} km 🔄",
    "search_session_expired": "⚠️ Sessione scaduta!\n\nUtilizza il comando /search per avviare una nuova ricerca.",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ Nessuna statistica disponibile!\n\nUtilizza il comando /search per avviare una ricerca.",
    "statistics": (
        "<b><u>Statistiche {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} ricerche</b> effettuate.\n"
        "<b>{num_stations} distributori</b> analizzati.\n"
        "Risparmio medio: <b>{avg_eur_save_per_unit} {price_unit}</b>, ovvero il <b>{avg_pct_save}%</b>.\n"
        "Risparmio annuo stimato: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>❓ Come abbiamo calcolato questi dati?</i>\n"
                       "• Il risparmio medio è calcolato come media del risparmio ottenuto in ogni ricerca, pari alla differenza tra il prezzo medio della zona e il prezzo del distributore più economico trovato.\n"
                       "• Il risparmio annuo è calcolato ipotizzando una percorrenza di 10.000km annui con un consumo medio di: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} ogni 100km",
    "reset_statistics": "Azzera le statistiche ♻️",
    "statistics_reset": "✅ Statistiche resettate correttamente!\n\nUtilizza il comando /search per avviare una ricerca.",

    "unknown_command_hint": "⚠️ Comando non valido!\n\nUtilizza il comando /help per l'elenco dei comandi disponibili.",

}
