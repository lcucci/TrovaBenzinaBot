import logging
from typing import Any, Dict, Optional

import aiohttp

from trovabenzina.config import MISE_SEARCH_URL, MISE_ROUTE_SEARCH_URL, MISE_TIMEOUT_SECONDS

__all__ = ["search_stations", "search_route_stations"]

log = logging.getLogger(__name__)


async def _post_search_request(url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Send a MISE search request and validate the response shape."""

    try:
        timeout = aiohttp.ClientTimeout(total=MISE_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    log.warning("MISE search failed (status=%s) url=%s payload=%s", resp.status, url, payload)
                    return None
                # MISE may reply with text/plain; ignore content-type to parse JSON safely.
                data = await resp.json(content_type=None)
                if not isinstance(data, dict) or not isinstance(data.get("results"), list):
                    log.warning("MISE search returned an invalid payload from %s: %s", url, data)
                    return None
                return data
    except Exception as exc:
        log.exception(
            "MISE search error (%s) url=%s payload=%s",
            type(exc).__name__,
            url,
            payload,
        )
        return None


async def search_stations(
        lat: float,
        lng: float,
        radius: float,
        fuel_type: str,
) -> Optional[Dict[str, Any]]:
    """Search fuel stations around a point using the MISE zone endpoint."""
    payload = {
        "points": [{"lat": lat, "lng": lng}],
        "radius": radius,
        "fuelType": fuel_type,
        "priceOrder": "asc",
    }
    return await _post_search_request(MISE_SEARCH_URL, payload)


async def search_route_stations(
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        fuel_type: str,
) -> Optional[Dict[str, Any]]:
    """Search fuel stations along a route using the MISE route endpoint."""
    payload = {
        "points": [
            {"lat": origin_lat, "lng": origin_lng},
            {"lat": destination_lat, "lng": destination_lng},
        ],
        "fuelType": fuel_type,
        "priceOrder": "asc",
    }
    return await _post_search_request(MISE_ROUTE_SEARCH_URL, payload)
