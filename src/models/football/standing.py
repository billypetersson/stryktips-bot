"""Standing model for league tables."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.football.season import Season


class Standing(Base):
    """Represents a league table/standings at a specific matchday.

    Stores the entire table as JSONB for flexibility.
    """

    __tablename__ = "football_standings"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Standing info
    matchday: Mapped[int] = mapped_column(Integer, nullable=False)

    # Table data stored as JSONB
    table: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # Example structure:
    # {
    #   "standings": [
    #     {
    #       "position": 1,
    #       "team_id": 123,
    #       "team_name": "Arsenal",
    #       "played": 10,
    #       "won": 8,
    #       "drawn": 1,
    #       "lost": 1,
    #       "goals_for": 25,
    #       "goals_against": 10,
    #       "goal_difference": 15,
    #       "points": 25,
    #       "form": ["W", "W", "D", "W", "W"]
    #     },
    #     ...
    #   ],
    #   "updated_at": "2025-10-25T20:00:00Z"
    # }

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="standings")

    # Indexes
    __table_args__ = (Index("ix_standing_season_matchday", "season_id", "matchday", unique=True),)

    def __repr__(self) -> str:
        return f"<Standing(id={self.id}, season_id={self.season_id}, matchday={self.matchday})>"
