"""Expert consensus service for aggregating expert predictions.

Collects predictions from multiple sources and calculates consensus picks
for each match in a Stryktips coupon.
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expert_item import ExpertItem
from src.models.match import Match
from src.models.coupon import Coupon
from src.providers.experts import (
    ExpertPrediction,
    RekatochklartProvider,
    AftonbladetProvider,
    StryktipsoddenProvider,
    ExpressenProvider,
    TipsmedossProvider,
    SpelbloggareProvider,
)

logger = logging.getLogger(__name__)


class ExpertConsensusService:
    """Service for managing expert predictions and calculating consensus.

    Responsibilities:
    - Fetch predictions from all enabled providers
    - Save predictions to database
    - Match predictions to matches in the database
    - Calculate consensus picks per match
    - Provide weighted consensus based on source reliability
    """

    # Source weights for weighted consensus (1.0 = neutral)
    # Higher weight = more reliable/respected source
    SOURCE_WEIGHTS = {
        "Rekatochklart": 1.2,  # Popular, well-regarded blog
        "Aftonbladet": 1.1,  # Major newspaper
        "Expressen": 1.1,  # Major newspaper
        "Stryktipspodden": 1.0,  # Podcast
        "Tipsmedoss": 1.0,  # Blog
        "Spelbloggare": 0.9,  # Platform with multiple bloggers
    }

    def __init__(
        self,
        db: AsyncSession,
        enabled_sources: Optional[list[str]] = None,
    ):
        """Initialize expert consensus service.

        Args:
            db: Database session
            enabled_sources: List of source names to use (None = use all)
        """
        self.db = db
        self.enabled_sources = enabled_sources or [
            "Rekatochklart",
            "Aftonbladet",
            "Stryktipspodden",
            "Expressen",
            "Tipsmedoss",
            "Spelbloggare",
        ]

        # Initialize providers
        self.providers = self._init_providers()

    def _init_providers(self) -> dict:
        """Initialize all enabled expert providers.

        Returns:
            Dictionary of provider instances by source name
        """
        all_providers = {
            "Rekatochklart": RekatochklartProvider(),
            "Aftonbladet": AftonbladetProvider(),
            "Stryktipspodden": StryktipsoddenProvider(),
            "Expressen": ExpressenProvider(),
            "Tipsmedoss": TipsmedossProvider(),
            "Spelbloggare": SpelbloggareProvider(),
        }

        # Filter to only enabled sources
        enabled_providers = {
            name: provider
            for name, provider in all_providers.items()
            if name in self.enabled_sources
        }

        logger.info(f"Initialized {len(enabled_providers)} expert providers: {', '.join(enabled_providers.keys())}")
        return enabled_providers

    async def fetch_and_save_latest_predictions(
        self, max_items_per_source: int = 20
    ) -> dict[str, int]:
        """Fetch latest predictions from all providers and save to database.

        Args:
            max_items_per_source: Max articles/episodes to fetch per source

        Returns:
            Dictionary with counts per source: {source_name: count}
        """
        logger.info("Fetching latest predictions from all providers")
        counts = {}

        for source_name, provider in self.providers.items():
            try:
                logger.info(f"Fetching from {source_name}...")
                predictions = await provider.fetch_latest_predictions(max_items_per_source)

                saved_count = await self._save_predictions(predictions)
                counts[source_name] = saved_count

                logger.info(f"Saved {saved_count} predictions from {source_name}")

            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}", exc_info=True)
                counts[source_name] = 0

        total = sum(counts.values())
        logger.info(f"Fetched and saved {total} total predictions from {len(counts)} sources")

        return counts

    async def _save_predictions(self, predictions: list[ExpertPrediction]) -> int:
        """Save predictions to database.

        Args:
            predictions: List of ExpertPrediction objects

        Returns:
            Number of predictions saved
        """
        saved_count = 0

        for pred in predictions:
            try:
                # Try to match to a match in the database
                match_id = await self._find_matching_match(
                    pred.match_home_team,
                    pred.match_away_team
                )

                # Create ExpertItem
                expert_item = ExpertItem(
                    source=pred.source,
                    author=pred.author,
                    published_at=pred.published_at,
                    url=pred.url,
                    match_id=match_id,
                    pick=pred.pick,
                    rationale=pred.rationale,
                    confidence=pred.confidence,
                    scraped_at=datetime.utcnow(),
                    raw_data=pred.raw_data,
                )

                # Check for duplicates (same URL + match)
                exists = await self.db.execute(
                    select(ExpertItem).where(
                        and_(
                            ExpertItem.url == pred.url,
                            ExpertItem.match_id == match_id if match_id else ExpertItem.match_id.is_(None)
                        )
                    )
                )

                if not exists.scalar_one_or_none():
                    self.db.add(expert_item)
                    saved_count += 1
                else:
                    logger.debug(f"Skipping duplicate prediction from {pred.url}")

            except Exception as e:
                logger.warning(f"Error saving prediction: {e}")
                continue

        await self.db.commit()
        return saved_count

    async def _find_matching_match(
        self, home_team: Optional[str], away_team: Optional[str]
    ) -> Optional[int]:
        """Find a match ID that matches the given team names.

        Uses fuzzy matching to handle variations in team names.

        Args:
            home_team: Home team name
            away_team: Away team name

        Returns:
            Match ID if found, None otherwise
        """
        if not home_team or not away_team:
            return None

        # Get active coupons (recent ones)
        cutoff_date = datetime.utcnow() - timedelta(days=14)

        result = await self.db.execute(
            select(Match)
            .join(Coupon)
            .where(
                and_(
                    Coupon.is_active == True,
                    Match.kickoff_time > cutoff_date
                )
            )
        )
        matches = result.scalars().all()

        # Try to find best match
        # Simple approach: normalize and compare
        home_normalized = self._normalize_team_for_matching(home_team)
        away_normalized = self._normalize_team_for_matching(away_team)

        for match in matches:
            match_home_norm = self._normalize_team_for_matching(match.home_team)
            match_away_norm = self._normalize_team_for_matching(match.away_team)

            if home_normalized == match_home_norm and away_normalized == match_away_norm:
                logger.debug(f"Matched '{home_team} - {away_team}' to match {match.id}")
                return match.id

        logger.debug(f"No match found for '{home_team} - {away_team}'")
        return None

    def _normalize_team_for_matching(self, team_name: str) -> str:
        """Normalize team name for fuzzy matching.

        Args:
            team_name: Raw team name

        Returns:
            Normalized team name
        """
        # Remove common suffixes and special characters
        normalized = team_name.lower()
        normalized = normalized.replace(" fc", "").replace(" if", "").replace(" bk", "")
        normalized = "".join(c for c in normalized if c.isalnum() or c.isspace())
        normalized = " ".join(normalized.split())  # Normalize whitespace

        return normalized

    async def get_consensus_for_match(self, match_id: int) -> dict:
        """Calculate consensus for a specific match.

        Args:
            match_id: Match ID

        Returns:
            Dictionary with consensus data
        """
        # Get all predictions for this match
        result = await self.db.execute(
            select(ExpertItem).where(ExpertItem.match_id == match_id)
        )
        predictions = result.scalars().all()

        if not predictions:
            return {
                "match_id": match_id,
                "prediction_count": 0,
                "consensus_pick": None,
                "confidence": 0.0,
                "pick_distribution": {},
                "weighted_consensus": None,
                "source_breakdown": {},
            }

        # Count picks
        picks = [p.pick for p in predictions]
        pick_counts = Counter(picks)

        # Simple consensus (most common pick)
        consensus_pick = pick_counts.most_common(1)[0][0]
        consensus_count = pick_counts[consensus_pick]
        confidence = consensus_count / len(predictions)

        # Weighted consensus
        weighted_picks = defaultdict(float)
        for pred in predictions:
            weight = self.SOURCE_WEIGHTS.get(pred.source, 1.0)
            weighted_picks[pred.pick] += weight

        weighted_consensus = max(weighted_picks.items(), key=lambda x: x[1])[0]

        # Source breakdown
        source_breakdown = defaultdict(list)
        for pred in predictions:
            source_breakdown[pred.source].append({
                "pick": pred.pick,
                "author": pred.author,
                "published_at": pred.published_at,
                "url": pred.url,
                "rationale": pred.rationale,
            })

        return {
            "match_id": match_id,
            "prediction_count": len(predictions),
            "consensus_pick": consensus_pick,
            "confidence": round(confidence, 2),
            "pick_distribution": dict(pick_counts),
            "weighted_consensus": weighted_consensus,
            "source_breakdown": dict(source_breakdown),
        }

    async def get_consensus_for_coupon(self, coupon_id: int) -> list[dict]:
        """Calculate consensus for all matches in a coupon.

        Args:
            coupon_id: Coupon ID

        Returns:
            List of consensus data per match
        """
        # Get all matches for this coupon
        result = await self.db.execute(
            select(Match).where(Match.coupon_id == coupon_id).order_by(Match.match_number)
        )
        matches = result.scalars().all()

        consensus_list = []
        for match in matches:
            consensus = await self.get_consensus_for_match(match.id)
            consensus["match_number"] = match.match_number
            consensus["home_team"] = match.home_team
            consensus["away_team"] = match.away_team
            consensus_list.append(consensus)

        return consensus_list

    async def get_latest_predictions(
        self, limit: int = 50, source: Optional[str] = None
    ) -> list[ExpertItem]:
        """Get latest expert predictions from database.

        Args:
            limit: Maximum number of predictions to return
            source: Filter by source name (optional)

        Returns:
            List of ExpertItem objects
        """
        query = select(ExpertItem).order_by(ExpertItem.published_at.desc()).limit(limit)

        if source:
            query = query.where(ExpertItem.source == source)

        result = await self.db.execute(query)
        return result.scalars().all()
