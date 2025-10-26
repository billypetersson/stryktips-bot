"""Venue model for football stadiums and arenas."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.football.match import FootballMatch


class Venue(Base):
    """Represents a football stadium or arena.

    Examples: Old Trafford, Anfield, Emirates Stadium
    """

    __tablename__ = "venues"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Venue info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # External references (API IDs, etc.)
    external_refs: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Example: {"api_football": 789, "wikipedia": "Old_Trafford"}

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    matches: Mapped[list["FootballMatch"]] = relationship(
        "FootballMatch", back_populates="venue", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, name='{self.name}', city='{self.city}')>"
