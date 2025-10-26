"""Competition model for football leagues and tournaments."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.football.season import Season


class Competition(Base):
    """Represents a football competition (league or tournament).

    Examples: Premier League, Championship, FA Cup, etc.
    """

    __tablename__ = "competitions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Competition info
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 = top tier, 2 = second tier, etc.

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    seasons: Mapped[list["Season"]] = relationship(
        "Season", back_populates="competition", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Competition(id={self.id}, code='{self.code}', name='{self.name}')>"
