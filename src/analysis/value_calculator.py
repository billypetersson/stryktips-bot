"""Value calculator - computes expected value for each sign."""

import logging
from typing import Any
from sqlalchemy.orm import Session

from src.models import Match, Odds, Analysis
from src.config import settings

logger = logging.getLogger(__name__)


class ValueCalculator:
    """Calculate value for each sign based on odds and distribution."""

    def __init__(self, db: Session) -> None:
        """Initialize value calculator."""
        self.db = db
        self.min_value_threshold = settings.min_value_threshold

    def calculate_match_value(self, match: Match) -> Analysis | None:
        """
        Calculate value for a single match.

        Value = true_probability / streck_percentage

        A value > 1.0 indicates positive expected value.
        """
        if not match.odds:
            logger.warning(f"No odds available for match {match.match_number}")
            return None

        # Calculate average odds from all bookmakers
        avg_home = sum(o.home_odds for o in match.odds) / len(match.odds)
        avg_draw = sum(o.draw_odds for o in match.odds) / len(match.odds)
        avg_away = sum(o.away_odds for o in match.odds) / len(match.odds)

        # Convert odds to true probabilities (remove margin)
        raw_home_prob = 1 / avg_home
        raw_draw_prob = 1 / avg_draw
        raw_away_prob = 1 / avg_away
        total = raw_home_prob + raw_draw_prob + raw_away_prob

        true_home_prob = raw_home_prob / total
        true_draw_prob = raw_draw_prob / total
        true_away_prob = raw_away_prob / total

        # Calculate value compared to distribution (streckprocent)
        home_value = None
        draw_value = None
        away_value = None

        if match.home_percentage and match.home_percentage > 0:
            home_value = true_home_prob / (match.home_percentage / 100)

        if match.draw_percentage and match.draw_percentage > 0:
            draw_value = true_draw_prob / (match.draw_percentage / 100)

        if match.away_percentage and match.away_percentage > 0:
            away_value = true_away_prob / (match.away_percentage / 100)

        # Determine recommended signs based on value
        recommended_signs = self._determine_recommended_signs(
            home_value, draw_value, away_value
        )

        # Create or update analysis
        analysis = Analysis(
            match_id=match.id,
            avg_home_odds=avg_home,
            avg_draw_odds=avg_draw,
            avg_away_odds=avg_away,
            true_home_prob=true_home_prob,
            true_draw_prob=true_draw_prob,
            true_away_prob=true_away_prob,
            home_value=home_value,
            draw_value=draw_value,
            away_value=away_value,
            recommended_signs=recommended_signs,
        )

        logger.info(
            f"Match {match.match_number}: {match.home_team} - {match.away_team} "
            f"-> Recommended: {recommended_signs} "
            f"(Values: 1={(home_value if home_value is not None else 0.0):.2f}, "
            f"X={(draw_value if draw_value is not None else 0.0):.2f}, "
            f"2={(away_value if away_value is not None else 0.0):.2f})"
        )

        return analysis

    def _determine_recommended_signs(
        self,
        home_value: float | None,
        draw_value: float | None,
        away_value: float | None,
    ) -> str:
        """
        Determine which sign(s) to recommend based on value.

        Returns:
            String like '1', 'X', '2', '1X', '12', 'X2', or '1X2'
        """
        threshold = self.min_value_threshold
        recommended = []

        if home_value and home_value >= threshold:
            recommended.append("1")
        if draw_value and draw_value >= threshold:
            recommended.append("X")
        if away_value and away_value >= threshold:
            recommended.append("2")

        if not recommended:
            # No value found - pick the highest probability
            values = [
                (home_value or 0, "1"),
                (draw_value or 0, "X"),
                (away_value or 0, "2"),
            ]
            values.sort(reverse=True)
            recommended = [values[0][1]]

        return "".join(recommended)

    def calculate_all_matches(self, coupon_id: int) -> list[Analysis]:
        """
        Calculate value for all matches on a coupon.

        Args:
            coupon_id: ID of the coupon to analyze

        Returns:
            List of Analysis objects
        """
        from src.models import Coupon

        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            raise ValueError(f"Coupon {coupon_id} not found")

        analyses = []
        for match in coupon.matches:
            analysis = self.calculate_match_value(match)
            if analysis:
                analyses.append(analysis)
                self.db.add(analysis)

        self.db.commit()
        logger.info(f"Calculated value for {len(analyses)} matches on coupon {coupon_id}")

        return analyses
