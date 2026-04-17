import os

# Bot startup mode: "POLLING" (long-polling) or "WEBHOOK"
TB_MODE = os.getenv("TB_MODE", "WEBHOOK")

# Database connection URL (e.g. postgresql+asyncpg://user:pass@host:port/dbname)
DATABASE_URL = os.getenv("DATABASE_URL")

# Port to bind the HTTP server on when running in WEBHOOK mode
PORT = int(os.getenv("PORT", "8080"))

# Telegram webhook base URL
BASE_URL = os.getenv("BASE_URL")

# URL path segment to receive webhook updates (joined with BASE_URL)
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "webhook")

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Telegram admin allowed to trigger manual broadcast delivery
_BROADCAST_ADMIN_TG_ID = os.getenv("BROADCAST_ADMIN_TG_ID", "").strip()
BROADCAST_ADMIN_TG_ID = int(_BROADCAST_ADMIN_TG_ID) if _BROADCAST_ADMIN_TG_ID else 0

# Default fallback language
DEFAULT_LANGUAGE = "it"

# In‐memory maps, populated at startup from the database
FUEL_MAP = {}
LANGUAGE_MAP = {}

# MISE API endpoints
MISE_SEARCH_URL = os.getenv(
    "MISE_SEARCH_URL",
    "https://carburanti.mise.gov.it/ospzApi/search/zone"
)
MISE_ROUTE_SEARCH_URL = os.getenv(
    "MISE_ROUTE_SEARCH_URL",
    "https://carburanti.mise.gov.it/ospzApi/search/route"
)
MISE_DETAIL_URL = os.getenv(
    "MISE_DETAIL_URL",
    "https://carburanti.mise.gov.it/ospzApi/registry/servicearea/{id}"
)
MISE_TIMEOUT_SECONDS = float(os.getenv("MISE_TIMEOUT_SECONDS", "30"))

# Google Maps Geocoding API endpoint
MAPS_GEOCODING_URL = os.getenv(
    "GEOCODE_URL",
    "https://maps.googleapis.com/maps/api/geocode/json"
)

# Geocoding cache: maximum number of monthly requests to cache
GEOCODE_HARD_CAP = int(os.getenv("GEOCODE_HARD_CAP", "10000"))

# Donation feature toggle and PayPal link
ENABLE_DONATION = os.getenv("ENABLE_DONATION", "true").lower() == "true"
PAYPAL_LINK = os.getenv("PAYPAL_LINK", "https://www.paypal.com/donate")
