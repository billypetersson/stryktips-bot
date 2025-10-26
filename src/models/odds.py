"""Odds model - stores odds from various bookmakers."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.match import Match


class Odds(Base):
    """Odds from a specific bookmaker for a match."""

    __tablename__ = "odds"
    __table_args__ = (
        UniqueConstraint("match_id", "bookmaker", name="uix_match_bookmaker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bookmaker: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Odds values
    home_odds: Mapped[float] = mapped_column(Float, nullable=False)
    draw_odds: Mapped[float] = mapped_column(Float, nullable=False)
    away_odds: Mapped[float] = mapped_column(Float, nullable=False)

    # Implied probabilities (calculated from odds)
    home_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    draw_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_probability: Mapped[float | None] = mapped_column(Float, nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="odds")

    def __repr__(self) -> str:
        return f"<Odds({self.bookmaker}: {self.home_odds}/{self.draw_odds}/{self.away_odds})>"

    def calculate_implied_probabilities(self) -> None:
        """Calculate implied probabilities from odds (removing bookmaker margin)."""
        raw_home = 1 / self.home_odds
        raw_draw = 1 / self.draw_odds
        raw_away = 1 / self.away_odds
        total = raw_home + raw_draw + raw_away

        # Normalize to remove margin
        self.home_probability = raw_home / total
        self.draw_probability = raw_draw / total
        self.away_probability = raw_away / total
