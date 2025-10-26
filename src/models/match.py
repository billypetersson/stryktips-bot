"""Match model - represents a single match on a coupon."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.coupon import Coupon
    from src.models.odds import Odds
    from src.models.expert import ExpertOpinion
    from src.models.analysis import Analysis


class Match(Base):
    """Individual match on a Stryktips coupon."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coupon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_number: Mapped[int] = mapped_column(Integer, nullable=False)

    home_team: Mapped[str] = mapped_column(String(200), nullable=False)
    away_team: Mapped[str] = mapped_column(String(200), nullable=False)
    kickoff_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Streckprocent från Svenska Spel
    home_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    draw_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Result (populated after match)
    result: Mapped[str | None] = mapped_column(String(1), nullable=True)  # '1', 'X', '2'

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    coupon: Mapped["Coupon"] = relationship("Coupon", back_populates="matches")
    odds: Mapped[list["Odds"]] = relationship(
        "Odds", back_populates="match", cascade="all, delete-orphan"
    )
    expert_opinions: Mapped[list["ExpertOpinion"]] = relationship(
        "ExpertOpinion", back_populates="match", cascade="all, delete-orphan"
    )
    analysis: Mapped["Analysis | None"] = relationship(
        "Analysis", back_populates="match", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Match({self.match_number}: {self.home_team} - {self.away_team})>"
