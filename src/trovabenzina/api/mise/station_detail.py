import logging
from typing import Optional

import aiohttp

from trovabenzina.config import MISE_DETAIL_URL

__all__ = ["get_station_address"]

log = logging.getLogger(__name__)


async def get_station_address(station_id: int) -> Optional[str]:
    """Fetch a station's full address from the MISE public registry.

    Args:
        station_id: Unique station identifier in the MISE registry.

    Returns:
        Optional[str]: The address string if found; otherwise None.
    """
    url = MISE_DETAIL_URL.format(id=station_id)

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    log.warning("MISE detail failed (status=%s) station_id=%s", resp.status, station_id)
                    return None
                data = await resp.json(content_type=None)
                return data.get("address") if isinstance(data, dict) else None
    except Exception as exc:
        log.exception(
            "Error fetching MISE detail for station %s (%s) url=%s",
            station_id,
            type(exc).__name__,
            url,
        )
        return None

