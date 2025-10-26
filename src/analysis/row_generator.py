"""Row generator - creates optimal Stryktips rows."""

import logging
from itertools import product
from typing import Any
from sqlalchemy.orm import Session

from src.models import Coupon, Analysis, SuggestedRow
from src.config import settings

logger = logging.getLogger(__name__)


class RowGenerator:
    """Generate optimal Stryktips rows with constrained half covers."""

    def __init__(self, db: Session) -> None:
        """Initialize row generator."""
        self.db = db
        self.max_half_covers = settings.max_half_covers

    def generate_rows(self, coupon_id: int, max_rows: int = 3) -> list[SuggestedRow]:
        """
        Generate optimal rows for a coupon.

        Strategy:
        1. Use recommended signs from value analysis
        2. Allow up to max_half_covers matches with half covers (2 signs)
        3. Optimize for expected value while keeping cost reasonable

        Args:
            coupon_id: ID of the coupon
            max_rows: Maximum number of rows to generate

        Returns:
            List of suggested rows
        """
        coupon = self.db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            raise ValueError(f"Coupon {coupon_id} not found")

        # Get analyses for all matches
        analyses = {
            match.match_number: match.analysis
            for match in coupon.matches
            if match.analysis
        }

        if len(analyses) != 13:
            logger.warning(
                f"Only {len(analyses)} matches analyzed out of 13, generating rows anyway"
            )

        # Generate primary row (most conservative - highest value single signs)
        primary_row = self._generate_primary_row(analyses)

        # Generate alternative rows with strategic half covers
        alternative_rows = self._generate_alternative_rows(analyses, max_rows - 1)

        all_rows = [primary_row] + alternative_rows

        # Save suggested rows to database
        saved_rows = []
        for row_data in all_rows:
            suggested_row = SuggestedRow(
                coupon_id=coupon_id,
                row_data=row_data["row"],
                half_cover_count=row_data["half_cover_count"],
                expected_value=row_data["expected_value"],
                cost_factor=row_data["cost_factor"],
                reasoning=row_data["reasoning"],
            )
            self.db.add(suggested_row)
            saved_rows.append(suggested_row)

        self.db.commit()
        logger.info(f"Generated {len(saved_rows)} rows for coupon {coupon_id}")

        return saved_rows

    def _generate_primary_row(self, analyses: dict[int, Analysis]) -> dict[str, Any]:
        """
        Generate primary row using highest value single signs.

        This is the most conservative approach - one sign per match.
        """
        row: dict[int, str] = {}
        total_value = 0.0

        for match_num in range(1, 14):
            if match_num not in analyses:
                row[match_num] = "1"  # Default fallback
                continue

            analysis = analyses[match_num]
            recommended = analysis.recommended_signs

            # Take first sign if multiple recommended
            if len(recommended) > 1:
                # Choose the one with highest value
                values = [
                    (analysis.home_value or 0, "1"),
                    (analysis.draw_value or 0, "X"),
                    (analysis.away_value or 0, "2"),
                ]
                values.sort(reverse=True)
                row[match_num] = values[0][1]
                total_value += values[0][0]
            else:
                row[match_num] = recommended
                # Add corresponding value
                if recommended == "1":
                    total_value += analysis.home_value or 0
                elif recommended == "X":
                    total_value += analysis.draw_value or 0
                elif recommended == "2":
                    total_value += analysis.away_value or 0

        return {
            "row": row,
            "half_cover_count": 0,
            "expected_value": total_value / 13,  # Average value per match
            "cost_factor": 1,  # Single row
            "reasoning": "Primär rad med högsta värdet per match. Inga helgarderingar.",
        }

    def _generate_alternative_rows(
        self, analyses: dict[int, Analysis], num_rows: int
    ) -> list[dict[str, Any]]:
        """
        Generate alternative rows with strategic half covers.

        Strategy: Add half covers on matches where:
        1. Multiple signs have good value
        2. Experts are divided
        3. Odds are close (uncertain outcome)
        """
        if num_rows <= 0:
            return []

        # Identify matches suitable for half covers
        half_cover_candidates = []

        for match_num in range(1, 14):
            if match_num not in analyses:
                continue

            analysis = analyses[match_num]
            values = [
                (analysis.home_value or 0, "1"),
                (analysis.draw_value or 0, "X"),
                (analysis.away_value or 0, "2"),
            ]
            values.sort(reverse=True)

            # Good candidate if top 2 values are close
            if len(values) >= 2 and values[0][0] > 0 and values[1][0] > 0:
                value_ratio = values[1][0] / values[0][0]
                if value_ratio >= 0.7:  # Top 2 within 30% of each other
                    half_cover_candidates.append({
                        "match_num": match_num,
                        "signs": values[0][1] + values[1][1],
                        "combined_value": values[0][0] + values[1][0],
                    })

        # Sort by combined value
        half_cover_candidates.sort(key=lambda x: x["combined_value"], reverse=True)

        # Generate alternative rows
        alternative_rows = []

        # Row 2: Add half cover on best candidate
        if half_cover_candidates:
            row2 = self._build_row_with_half_covers(
                analyses, half_cover_candidates[:1]
            )
            alternative_rows.append(row2)

        # Row 3: Add half covers on best 2 candidates
        if len(half_cover_candidates) >= 2 and num_rows >= 2:
            row3 = self._build_row_with_half_covers(
                analyses, half_cover_candidates[:2]
            )
            alternative_rows.append(row3)

        return alternative_rows[:num_rows]

    def _build_row_with_half_covers(
        self, analyses: dict[int, Analysis], half_covers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build a row with specified half covers."""
        row: dict[int, str] = {}
        total_value = 0.0
        half_cover_matches = {hc["match_num"] for hc in half_covers}

        for match_num in range(1, 14):
            if match_num in half_cover_matches:
                # Use half cover
                hc = next(hc for hc in half_covers if hc["match_num"] == match_num)
                row[match_num] = hc["signs"]
                total_value += hc["combined_value"]
            elif match_num in analyses:
                # Use single sign
                analysis = analyses[match_num]
                values = [
                    (analysis.home_value or 0, "1"),
                    (analysis.draw_value or 0, "X"),
                    (analysis.away_value or 0, "2"),
                ]
                values.sort(reverse=True)
                row[match_num] = values[0][1]
                total_value += values[0][0]
            else:
                row[match_num] = "1"  # Fallback

        cost_factor = 2 ** len(half_covers)  # Each half cover doubles the cost

        return {
            "row": row,
            "half_cover_count": len(half_covers),
            "expected_value": total_value / 13,
            "cost_factor": cost_factor,
            "reasoning": (
                f"Alternativ rad med {len(half_covers)} helgardering(ar) "
                f"på matcher: {', '.join(str(hc['match_num']) for hc in half_covers)}. "
                f"Kostnad: {cost_factor}x basinvestering."
            ),
        }
