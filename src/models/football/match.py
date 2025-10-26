"""Match model for football matches."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.football.season import Season
    from src.models.football.team import Team
    from src.models.football.venue import Venue
    from src.models.football.event import Event


class FootballMatch(Base):
    """Represents a football match in a competition.

    Note: Named 'FootballMatch' to avoid collision with existing Match model for Stryktips.
    """

    __tablename__ = "football_matches"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Match info
    matchday: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Round/gameweek number
    date_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="scheduled"
    )  # scheduled, live, finished, postponed, cancelled

    # Score
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # External references and metadata
    external_refs: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Example: {"api_football": 12345, "flashscore": "xyz"}

    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Where data came from
    source_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # When data was fetched

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="matches")
    home_team: Mapped["Team"] = relationship(
        "Team", back_populates="home_matches", foreign_keys=[home_team_id]
    )
    away_team: Mapped["Team"] = relationship(
        "Team", back_populates="away_matches", foreign_keys=[away_team_id]
    )
    venue: Mapped["Venue | None"] = relationship("Venue", back_populates="matches")
    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="match", cascade="all, delete-orphan"
    )

    # Unique constraint: prevent duplicate matches
    __table_args__ = (
        UniqueConstraint(
            "season_id",
            "matchday",
            "home_team_id",
            "away_team_id",
            name="uq_match_season_matchday_teams",
        ),
        Index("ix_match_season_date", "season_id", "date_utc"),
        Index("ix_match_teams", "home_team_id", "away_team_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<FootballMatch(id={self.id}, "
            f"home_team_id={self.home_team_id}, "
            f"away_team_id={self.away_team_id}, "
            f"date={self.date_utc.date()})>"
        )
