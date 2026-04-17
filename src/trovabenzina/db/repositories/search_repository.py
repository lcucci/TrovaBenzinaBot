"""Search repository: writes and analytics helpers for searches."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select, update

from ..models import Search, User, Fuel
from ..session import AsyncSession


async def save_search(
        tg_id: int,
        fuel_code: str,
        radius: Optional[float],
        num_stations: int,
        price_avg: Optional[float] = None,
        price_min: Optional[float] = None,
        search_type: str = "zone",
) -> None:
    """Persist a search record linked to the given Telegram user.

    Args:
        tg_id: Telegram user ID.
        fuel_code: Fuel code for the search.
        radius: Search radius (km), or None for route searches.
        num_stations: Number of stations considered.
        price_avg: Average price among stations (optional).
        price_min: Minimum price among stations (optional).
        search_type: Search kind persisted for analytics ('zone' or 'route').

    Raises:
        sqlalchemy.exc.NoResultFound: If the user or fuel cannot be resolved.
    """
    async with AsyncSession() as session:
        user_id = (await session.execute(
            select(User.id).where(User.tg_id == tg_id)
        )).scalar_one()

        fuel_id = (await session.execute(
            select(Fuel.id).where(Fuel.code == fuel_code)
        )).scalar_one()

        new_search = Search(
            user_id=user_id,
            fuel_id=fuel_id,
            search_type=search_type,
            radius=radius,
            num_stations=num_stations,
            price_avg=price_avg,
            price_min=price_min,
        )
        session.add(new_search)
        await session.commit()


async def soft_delete_user_searches(user_id: int) -> int:
    """Soft-delete all active searches for a given user.

    Args:
        user_id: Internal `User.id`.

    Returns:
        int: Number of rows updated.
    """
    async with AsyncSession() as session:
        res = await session.execute(
            update(Search)
            .where(Search.user_id == user_id)
            .where(Search.del_ts.is_(None))
            .values(del_ts=func.now())
        )
        await session.commit()
        return res.rowcount or 0


async def soft_delete_user_searches_by_tg_id(tg_id: int) -> int:
    """Soft-delete all active searches for a given Telegram user.

    Args:
        tg_id: Telegram user ID.

    Returns:
        int: Number of rows updated.
    """
    async with AsyncSession() as session:
        user_id = (await session.execute(
            select(User.id).where(User.tg_id == tg_id)
        )).scalar_one()

    return await soft_delete_user_searches(user_id)
