"""Test database models."""

from datetime import datetime
from sqlalchemy.orm import Session

from src.models import Coupon, Match, Odds, Analysis


def test_create_coupon(db_session: Session) -> None:
    """Test creating a coupon."""
    coupon = Coupon(
        week_number=42,
        year=2025,
        draw_date=datetime(2025, 10, 25, 18, 0),
        jackpot_amount=10_000_000,
    )
    db_session.add(coupon)
    db_session.commit()

    assert coupon.id is not None
    assert coupon.week_number == 42
    assert coupon.is_active is True


def test_create_match(db_session: Session) -> None:
    """Test creating a match."""
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
        home_team="AIK",
        away_team="Hammarby",
        kickoff_time=datetime(2025, 10, 25, 15, 0),
        home_percentage=35.0,
        draw_percentage=30.0,
        away_percentage=35.0,
    )
    db_session.add(match)
    db_session.commit()

    assert match.id is not None
    assert match.home_team == "AIK"
    assert match.coupon.week_number == 42


def test_odds_probability_calculation(db_session: Session) -> None:
    """Test odds implied probability calculation."""
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
    )
    db_session.add(match)
    db_session.flush()

    odds = Odds(
        match_id=match.id,
        bookmaker="Test Bookmaker",
        home_odds=2.0,
        draw_odds=3.5,
        away_odds=3.0,
    )
    odds.calculate_implied_probabilities()
    db_session.add(odds)
    db_session.commit()

    assert odds.home_probability is not None
    assert odds.draw_probability is not None
    assert odds.away_probability is not None

    # Probabilities should sum to 1.0 (within rounding error)
    total = odds.home_probability + odds.draw_probability + odds.away_probability
    assert abs(total - 1.0) < 0.001
