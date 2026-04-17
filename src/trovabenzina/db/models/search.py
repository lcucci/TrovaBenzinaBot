from __future__ import annotations

"""Search analytics entity."""

from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Numeric, ForeignKey, Integer, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .fuel import Fuel

__all__ = ["Search"]


class Search(TimestampMixin, Base):
    """A single search event recorded for analytics."""

    __tablename__ = "searches"
    __table_args__ = (
        CheckConstraint("(radius IS NULL OR radius >= 0)", name="ck_search_radius_nonneg"),
        CheckConstraint("num_stations >= 0", name="ck_search_num_stations_nonneg"),
        CheckConstraint("search_type IN ('zone', 'route')", name="ck_search_type_valid"),
        CheckConstraint(
            "(price_avg IS NULL OR price_min IS NULL OR price_avg >= price_min)",
            name="ck_search_price_avg_gte_min",
        ),
        CheckConstraint("(price_avg IS NULL OR price_avg >= 0)", name="ck_search_price_avg_nonneg"),
        CheckConstraint("(price_min IS NULL OR price_min >= 0)", name="ck_search_price_min_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    fuel_id: Mapped[int] = mapped_column(ForeignKey("dom_fuels.id"), nullable=False)
    search_type: Mapped[str] = mapped_column(String(10), nullable=False, server_default="zone")

    radius: Mapped[Optional[float]] = mapped_column(nullable=True)
    num_stations: Mapped[int] = mapped_column(Integer, nullable=False)
    price_avg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    price_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="searches", lazy="joined")
    fuel: Mapped["Fuel"] = relationship(back_populates="searches", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"Search(id={self.id}, user_id={self.user_id}, fuel_id={self.fuel_id}, "
            f"search_type={self.search_type}, radius={self.radius}, num_stations={self.num_stations}, "
            f"price_avg={self.price_avg}, price_min={self.price_min})"
        )
