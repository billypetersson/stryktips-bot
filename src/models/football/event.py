"""Event model for match events (goals, cards, substitutions, etc.)."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.football.match import FootballMatch
    from src.models.football.team import Team


class Event(Base):
    """Represents an event during a football match.

    Examples: goal, yellow card, red card, substitution, penalty
    """

    __tablename__ = "football_events"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    match_id: Mapped[int] = mapped_column(
        ForeignKey("football_matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Event info
    minute: Mapped[int] = mapped_column(Integer, nullable=False)  # Minute in match (can be 90+3, etc.)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: goal, penalty, own_goal, yellow_card, red_card, substitution, var_decision, etc.

    player: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Player name

    # Additional details (assists, reason for card, substitution info, etc.)
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Example for goal: {"assist": "Player Name", "type": "header", "penalty": false}
    # Example for substitution: {"player_out": "Name A", "player_in": "Name B"}
    # Example for card: {"reason": "foul", "var_check": true}

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    match: Mapped["FootballMatch"] = relationship("FootballMatch", back_populates="events")
    team: Mapped["Team"] = relationship("Team", back_populates="events")

    # Indexes
    __table_args__ = (
        Index("ix_event_match_minute", "match_id", "minute"),
        Index("ix_event_type", "type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Event(id={self.id}, "
            f"type='{self.type}', "
            f"minute={self.minute}, "
            f"player='{self.player}')>"
        )
