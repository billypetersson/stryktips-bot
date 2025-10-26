"""Add test match to next week's coupon."""
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.config import settings
from src.models.coupon import Coupon
from src.models.match import Match
from src.models.odds import Odds
from src.models.expert import ExpertOpinion

# Match data
match_data = {
    "home_team": "Liverpool",
    "away_team": "Aston Villa",
    "match_number": 1,
    "match_time": datetime.now() + timedelta(days=7),  # Next week
    "odds": {
        "bookmaker": "test",
        "odds_1": 1.57,
        "odds_x": 4.75,
        "odds_2": 5.60,
    },
    "svenska_folket": {
        "percent_1": 51,
        "percent_x": 22,
        "percent_2": 27,
    }
}

engine = create_engine(settings.database_url)

with Session(engine) as session:
    # Get or create coupon for week 44
    coupon = session.execute(
        select(Coupon).where(Coupon.week_number == 44, Coupon.year == 2025)
    ).scalar_one_or_none()

    if not coupon:
        print("Creating coupon for week 44, 2025...")
        coupon = Coupon(
            week_number=44,
            year=2025,
            draw_date=datetime.now() + timedelta(days=7),
            is_active=True,
        )
        session.add(coupon)
        session.flush()
        print(f"✓ Created coupon: {coupon}")
    else:
        print(f"✓ Using existing coupon: {coupon}")

    # Check if match already exists
    existing_match = session.execute(
        select(Match).where(
            Match.coupon_id == coupon.id,
            Match.match_number == match_data["match_number"]
        )
    ).scalar_one_or_none()

    if existing_match:
        print(f"Match {match_data['match_number']} already exists, deleting...")
        session.delete(existing_match)
        session.flush()

    # Create match
    print(f"Creating match: {match_data['home_team']} - {match_data['away_team']}...")
    match = Match(
        coupon_id=coupon.id,
        match_number=match_data["match_number"],
        home_team=match_data["home_team"],
        away_team=match_data["away_team"],
        kickoff_time=match_data["match_time"],
        home_percentage=match_data["svenska_folket"]["percent_1"],
        draw_percentage=match_data["svenska_folket"]["percent_x"],
        away_percentage=match_data["svenska_folket"]["percent_2"],
    )
    session.add(match)
    session.flush()
    print(f"✓ Created match: {match}")

    # Add odds
    print("Adding odds...")
    odds = Odds(
        match_id=match.id,
        bookmaker=match_data["odds"]["bookmaker"],
        home_odds=match_data["odds"]["odds_1"],
        draw_odds=match_data["odds"]["odds_x"],
        away_odds=match_data["odds"]["odds_2"],
    )
    # Calculate implied probabilities
    odds.calculate_implied_probabilities()
    session.add(odds)
    print(f"✓ Added odds: 1={odds.home_odds}, X={odds.draw_odds}, 2={odds.away_odds}")

    # Commit
    session.commit()
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"Match added to week {coupon.week_number}, {coupon.year}")
    print(f"{match.match_number}. {match.home_team} - {match.away_team}")
    print(f"Kickoff: {match.kickoff_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Odds: 1={odds.home_odds} X={odds.draw_odds} 2={odds.away_odds}")
    print(f"Svenska folket: 1={match.home_percentage}% X={match.draw_percentage}% 2={match.away_percentage}%")
