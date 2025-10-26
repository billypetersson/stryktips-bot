"""Expert opinion model - stores expert predictions."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.match import Match


class ExpertOpinion(Base):
    """Expert opinion/prediction for a match."""

    __tablename__ = "expert_opinions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )

    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    expert_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    prediction: Mapped[str] = mapped_column(String(10), nullable=False)  # '1', 'X', '2', '1X', etc.

    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="expert_opinions")

    def __repr__(self) -> str:
        return f"<ExpertOpinion({self.source}: {self.prediction})>"
