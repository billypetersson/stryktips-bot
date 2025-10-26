"""Analysis models - value calculations and suggested rows."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.match import Match
    from src.models.coupon import Coupon


class Analysis(Base):
    """Value analysis for a specific match."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Average odds from all bookmakers
    avg_home_odds: Mapped[float] = mapped_column(Float, nullable=False)
    avg_draw_odds: Mapped[float] = mapped_column(Float, nullable=False)
    avg_away_odds: Mapped[float] = mapped_column(Float, nullable=False)

    # True probabilities (from odds)
    true_home_prob: Mapped[float] = mapped_column(Float, nullable=False)
    true_draw_prob: Mapped[float] = mapped_column(Float, nullable=False)
    true_away_prob: Mapped[float] = mapped_column(Float, nullable=False)

    # Value calculations (true_prob / streck_prob)
    home_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    draw_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Best sign(s) based on value
    recommended_signs: Mapped[str] = mapped_column(String(10), nullable=False)  # '1', 'X', '2', '1X', etc.

    # Expert consensus summary
    expert_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<Analysis(match={self.match_id}, recommended={self.recommended_signs})>"


class SuggestedRow(Base):
    """Generated Stryktips row suggestion."""

    __tablename__ = "suggested_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coupon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Row as JSON: {1: '1', 2: 'X', 3: '12', ...}
    row_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Number of half covers (helgarderingar)
    half_cover_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Expected value metrics
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    cost_factor: Mapped[int] = mapped_column(Integer, nullable=False)  # Number of combinations

    # Reasoning
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    coupon: Mapped["Coupon"] = relationship("Coupon")

    def __repr__(self) -> str:
        return f"<SuggestedRow(coupon={self.coupon_id}, value={self.expected_value:.2f})>"
