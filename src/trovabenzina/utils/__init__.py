"""Public exports for the :mod:`utils` package.

This file re-exports convenience functions and constants so they can be
imported as ``from trovabenzina.utils import ...``.
"""

from .formatting import (
    symbol_eur,
    symbol_kilo,
    symbol_liter,
    symbol_slash,
    format_price,
    format_price_unit,
    pct_delta_from_avg,
    format_avg_comparison_text,
    format_date,
    format_directions_url,
    format_radius,
)
from .logging import RailwayLogFormatter, describe, setup_logging
from .routing import reroute_command
from .states import (
    STEP_PROFILE_FUEL,
    STEP_PROFILE_LANGUAGE,
    STEP_PROFILE_MENU,
    STEP_SEARCH_MODE,
    STEP_SEARCH_LOCATION,
    STEP_SEARCH_ROUTE_ORIGIN,
    STEP_SEARCH_ROUTE_DESTINATION,
    STEP_START_FUEL,
    STEP_START_LANGUAGE,
)
from .telegram import (
    inline_kb,
    inline_menu_from_map,
    with_back_row,
    remember_profile_message,
    delete_last_profile_message,
)

__all__ = [
    # formatting
    "symbol_eur",
    "symbol_slash",
    "symbol_liter",
    "symbol_kilo",
    "format_price",
    "format_price_unit",
    "pct_delta_from_avg",
    "format_avg_comparison_text",
    "format_date",
    "format_directions_url",
    "format_radius",
    # logging
    "RailwayLogFormatter",
    "setup_logging",
    "describe",
    # routing
    "reroute_command",
    # states
    "STEP_START_LANGUAGE",
    "STEP_START_FUEL",
    "STEP_SEARCH_MODE",
    "STEP_SEARCH_LOCATION",
    "STEP_SEARCH_ROUTE_ORIGIN",
    "STEP_SEARCH_ROUTE_DESTINATION",
    "STEP_PROFILE_MENU",
    "STEP_PROFILE_LANGUAGE",
    "STEP_PROFILE_FUEL",
    # telegram
    "inline_kb",
    "inline_menu_from_map",
    "with_back_row",
    "remember_profile_message",
    "delete_last_profile_message",
]
