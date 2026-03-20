"""Top-level exports for the `trovabenzina.db` package.

Expose:
- ORM models and mixins (Base, TimestampMixin, CodeNameMixin, entities, views)
- Session/engine helpers (engine, AsyncSession, init_db)
- Repository functions (get_user, save_search, maps, stats, geocache, etc.)
"""

# Models
from .models import (
    Base,
    BroadcastMessage,
    TimestampMixin,
    CodeNameMixin,
    Fuel,
    Language,
    User,
    Search,
    GeoCache,
    VGeocodingMonthCalls,
    VUsersSearchesStats,
)
# Repository functions (instead of legacy crud)
from .repositories import (
    # broadcasts
    claim_pending_broadcasts,
    finalize_broadcast_message,
    get_broadcast_recipient_tg_ids,
    # fuels
    get_fuel_map,
    get_fuels_by_ids_map,
    get_uom_by_code,
    get_fuel_name_by_code,
    # languages
    get_language_map,
    get_language_id_by_code,
    # users
    upsert_user,
    get_user,
    get_user_language_code_by_tg_id,
    get_user_fuel_code_by_tg_id,
    get_user_id_by_tg_id,
    get_search_users,
    soft_delete_user_searches,
    soft_delete_user_searches_by_tg_id,
    # searches
    save_search,
    # geocache
    get_geocache,
    save_geocache,
    delete_old_geocache,
    # stats views
    count_geocoding_month_calls,
    get_user_stats,
)
# Session
from .session import engine, AsyncSession, init_db
from .sync import sync_config_tables

__all__ = [
    # Models/mixins
    "Base",
    "BroadcastMessage",
    "TimestampMixin",
    "CodeNameMixin",
    "Fuel",
    "Language",
    "User",
    "Search",
    "GeoCache",
    "VGeocodingMonthCalls",
    "VUsersSearchesStats",
    # Session
    "engine",
    "AsyncSession",
    "init_db",
    # Repositories
    "claim_pending_broadcasts",
    "finalize_broadcast_message",
    "get_broadcast_recipient_tg_ids",
    "get_fuel_map",
    "get_fuels_by_ids_map",
    "get_uom_by_code",
    "get_fuel_name_by_code",
    "get_language_map",
    "get_language_id_by_code",
    "upsert_user",
    "get_user",
    "get_user_language_code_by_tg_id",
    "get_user_fuel_code_by_tg_id",
    "get_user_id_by_tg_id",
    "get_search_users",
    "save_search",
    "soft_delete_user_searches",
    "soft_delete_user_searches_by_tg_id",
    "get_geocache",
    "save_geocache",
    "delete_old_geocache",
    "count_geocoding_month_calls",
    "get_user_stats",
    # sync
    "sync_config_tables",
]