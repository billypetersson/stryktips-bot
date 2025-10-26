"""Coupon model - represents a weekly Stryktips coupon."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.match import Match


class Coupon(Base):
    """Stryktips coupon for a specific week."""

    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    draw_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    jackpot_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    matches: Mapped[list["Match"]] = relationship(
        "Match", back_populates="coupon", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Coupon(week={self.week_number}, year={self.year})>"
