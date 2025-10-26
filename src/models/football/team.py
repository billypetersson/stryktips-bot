"""Team model for football clubs."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.football.match import FootballMatch
    from src.models.football.event import Event


class Team(Base):
    """Represents a football team/club.

    Examples: Manchester United, Liverpool FC, Arsenal
    """

    __tablename__ = "teams"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Team info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_normalized: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True
    )  # Lowercase, no special chars for matching
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # External references (API IDs, etc.)
    external_refs: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Example: {"api_football": 123, "transfermarkt": 456, "wikipedia": "Arsenal_F.C."}

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    home_matches: Mapped[list["FootballMatch"]] = relationship(
        "FootballMatch",
        back_populates="home_team",
        foreign_keys="FootballMatch.home_team_id",
        cascade="all, delete-orphan"
    )
    away_matches: Mapped[list["FootballMatch"]] = relationship(
        "FootballMatch",
        back_populates="away_team",
        foreign_keys="FootballMatch.away_team_id",
        cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="team", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}')>"
