"""Public API surface for external consumers of the 'api' package.

Exposes:
- Google Maps Geocoding
- MISE search (fuel stations by zone, price-ordered)
- MISE station detail (address)
"""

from .googlemaps.geocoding import geocode_address, geocode_address_with_country
from .mise.station_detail import get_station_address
from .mise.stations_search import search_stations, search_route_stations

__all__ = [
    "geocode_address",
    "geocode_address_with_country",
    "search_stations",
    "search_route_stations",
    "get_station_address",
]
