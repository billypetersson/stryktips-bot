"""Season model for football competitions."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.football.competition import Competition
    from src.models.football.match import FootballMatch
    from src.models.football.standing import Standing


class Season(Base):
    """Represents a season of a football competition.

    Examples: Premier League 2023/2024, Championship 2024/2025
    """

    __tablename__ = "seasons"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Season info
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "2023/2024"
    year_start: Mapped[int] = mapped_column(Integer, nullable=False)
    year_end: Mapped[int] = mapped_column(Integer, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    competition: Mapped["Competition"] = relationship("Competition", back_populates="seasons")
    matches: Mapped[list["FootballMatch"]] = relationship(
        "FootballMatch", back_populates="season", cascade="all, delete-orphan"
    )
    standings: Mapped[list["Standing"]] = relationship(
        "Standing", back_populates="season", cascade="all, delete-orphan"
    )

    # Unique constraint: one season name per competition
    __table_args__ = (
        UniqueConstraint("competition_id", "name", name="uq_season_competition_name"),
        Index("ix_season_competition_year", "competition_id", "year_start", "year_end"),
    )

    def __repr__(self) -> str:
        return f"<Season(id={self.id}, name='{self.name}', competition_id={self.competition_id})>"
