"""Expert item model for storing expert predictions from various sources."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

if TYPE_CHECKING:
    from src.models.match import Match


class ExpertItem(Base):
    """Expert prediction item from external sources.

    Stores individual expert picks from various Swedish sports media,
    blogs, and podcasts.
    """

    __tablename__ = "expert_items"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Source information
    source: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # e.g., "Rekatochklart", "Aftonbladet", "Stryktipspodden"

    author: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # Expert/author name

    # Publication info
    published_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )

    url: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Source URL for attribution

    # Article metadata
    title: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Article/video/podcast title

    summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Brief summary or excerpt

    # Match reference (nullable for general articles)
    match_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Match tags for flexible matching (team names, tournaments, rounds)
    match_tags: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # e.g., {"teams": ["Liverpool", "Arsenal"], "tournament": "Premier League", "round": 10}

    # Prediction
    pick: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # '1', 'X', '2', '1X', '12', 'X2'

    rationale: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Expert's reasoning/explanation

    confidence: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g., "High", "Medium", "Low", or percentage

    # Metadata
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    raw_data: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Store raw scraped data for debugging

    # Relationships
    match: Mapped["Match | None"] = relationship("Match", backref="expert_items")

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_expert_items_source_published", "source", "published_at"),
        Index("ix_expert_items_match_source", "match_id", "source"),
    )

    def __repr__(self) -> str:
        author_str = f", author='{self.author}'" if self.author else ""
        return (
            f"<ExpertItem(id={self.id}, source='{self.source}'{author_str}, "
            f"pick='{self.pick}', published={self.published_at.date()})>"
        )
