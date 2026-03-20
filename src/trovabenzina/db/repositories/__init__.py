"""Public surface for the repositories package.

Expose high-level repository functions so callers can do:
    from trovabenzina.db.repositories import get_user, save_search
"""

from .broadcast_repository import (
    claim_pending_broadcasts,
    finalize_broadcast_message,
    get_broadcast_recipient_tg_ids,
)
from .fuel_repository import (
    get_fuel_map,
    get_fuels_by_ids_map,
    get_uom_by_code,
    get_fuel_name_by_code,
)
from .geocache_repository import get_geocache, save_geocache, delete_old_geocache
from .language_repository import get_language_map, get_language_id_by_code
from .search_repository import (
    save_search,
    soft_delete_user_searches,
    soft_delete_user_searches_by_tg_id,
)
from .stats_repository import count_geocoding_month_calls, get_user_stats
from .user_repository import (
    upsert_user,
    get_user,
    get_user_language_code_by_tg_id,
    get_user_fuel_code_by_tg_id,
    get_user_id_by_tg_id,
    get_search_users,
)

__all__ = [
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
]