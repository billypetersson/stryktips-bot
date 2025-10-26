"""Test analysis functionality."""

from datetime import datetime
from sqlalchemy.orm import Session

from src.models import Coupon, Match, Odds
from src.analysis.value_calculator import ValueCalculator


def test_value_calculator(db_session: Session) -> None:
    """Test value calculation."""
    # Create test data
    coupon = Coupon(
        week_number=42,
        year=2025,
        draw_date=datetime(2025, 10, 25, 18, 0),
    )
    db_session.add(coupon)
    db_session.flush()

    match = Match(
        coupon_id=coupon.id,
        match_number=1,
        home_team="Team A",
        away_team="Team B",
        kickoff_time=datetime(2025, 10, 25, 15, 0),
        home_percentage=40.0,  # 40% of people bet on home
        draw_percentage=30.0,
        away_percentage=30.0,
    )
    db_session.add(match)
    db_session.flush()

    # Add odds suggesting home is more likely than people think
    odds = Odds(
        match_id=match.id,
        bookmaker="Test",
        home_odds=1.8,  # Implies ~55% probability
        draw_odds=3.5,
        away_odds=4.0,
    )
    odds.calculate_implied_probabilities()
    db_session.add(odds)
    db_session.commit()

    # Calculate value
    calculator = ValueCalculator(db_session)
    analysis = calculator.calculate_match_value(match)

    assert analysis is not None
    assert analysis.home_value is not None
    # Home should have value since true prob (~55%) > streck (40%)
    assert analysis.home_value > 1.0
    assert "1" in analysis.recommended_signs
