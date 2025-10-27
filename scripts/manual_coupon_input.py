#!/usr/bin/env python3
"""Manual input script for Stryktips coupon data.

Usage:
    python scripts/manual_coupon_input.py --week 43 --year 2025

You can provide match data via:
1. Interactive input (prompted)
2. JSON file with match data
3. Simple text format
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.database.session import SessionLocal
from src.models import Coupon, Match, Odds, ExpertOpinion
from src.scrapers.odds_providers import fetch_all_odds
from src.scrapers.experts import fetch_all_expert_opinions
from src.analysis.value_calculator import ValueCalculator
from src.analysis.expert_summarizer import ExpertSummarizer
from src.analysis.row_generator import RowGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_simple_format(text: str) -> list[dict]:
    """
    Parse simple text format:

    1. Liverpool - Aston Villa | 53 21 26
    2. Tottenham - Man City | 30 25 45
    ...

    Returns list of match dicts.
    """
    matches = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        try:
            # Split match number
            parts = line.split('.', 1)
            match_num = int(parts[0].strip())
            rest = parts[1].strip()

            # Split teams and percentages
            teams_part, pct_part = rest.split('|')
            home, away = teams_part.split('-')
            percentages = pct_part.strip().split()

            matches.append({
                'match_number': match_num,
                'home_team': home.strip(),
                'away_team': away.strip(),
                'home_percentage': float(percentages[0]),
                'draw_percentage': float(percentages[1]),
                'away_percentage': float(percentages[2])
            })
        except Exception as e:
            logger.warning(f"Kunde inte parsa rad: {line} - {e}")
            continue

    return matches


def input_matches_interactive() -> list[dict]:
    """Interactive input of matches."""
    matches = []
    print("\n📝 Mata in matcher (tryck Enter på tom rad för att avsluta)")
    print("Format: Hemmalag - Bortalag | hem% oavgjort% borta%")
    print("Exempel: Liverpool - Aston Villa | 53 21 26\n")

    for i in range(1, 14):
        line = input(f"Match {i}: ").strip()
        if not line:
            break

        try:
            teams_part, pct_part = line.split('|')
            home, away = teams_part.split('-')
            percentages = pct_part.strip().split()

            matches.append({
                'match_number': i,
                'home_team': home.strip(),
                'away_team': away.strip(),
                'home_percentage': float(percentages[0]),
                'draw_percentage': float(percentages[1]),
                'away_percentage': float(percentages[2]),
                'kickoff_time': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"❌ Fel format: {e}")
            print("Försök igen med format: Hemmalag - Bortalag | hem% oavgjort% borta%")
            i -= 1

    return matches


def create_coupon_from_manual_input(
    week_number: int,
    year: int,
    matches: list[dict],
    db: Session
) -> Coupon:
    """Create coupon from manual match input."""

    # Deactivate old coupons
    old_coupons = db.query(Coupon).filter(Coupon.is_active == True).all()
    for old_coupon in old_coupons:
        old_coupon.is_active = False
        logger.info(f"Deactivated old coupon: week {old_coupon.week_number}")

    # Create new coupon
    coupon = Coupon(
        week_number=week_number,
        year=year,
        draw_date=datetime.now(),
        is_active=True,
        jackpot_amount=None  # Can be set later
    )
    db.add(coupon)
    db.flush()

    logger.info(f"✅ Created coupon for week {week_number}/{year}")

    # Add matches
    for match_data in matches:
        match = Match(
            coupon_id=coupon.id,
            match_number=match_data['match_number'],
            home_team=match_data['home_team'],
            away_team=match_data['away_team'],
            kickoff_time=match_data.get('kickoff_time', datetime.now()),
            home_percentage=match_data.get('home_percentage'),
            draw_percentage=match_data.get('draw_percentage'),
            away_percentage=match_data.get('away_percentage')
        )
        db.add(match)

    db.commit()
    logger.info(f"✅ Added {len(matches)} matches to coupon")

    return coupon


def main():
    parser = argparse.ArgumentParser(description='Manual Stryktips coupon input')
    parser.add_argument('--week', type=int, required=True, help='Week number')
    parser.add_argument('--year', type=int, default=datetime.now().year, help='Year')
    parser.add_argument('--file', type=str, help='JSON/text file with match data')
    parser.add_argument('--text', type=str, help='Text string with match data')
    parser.add_argument('--run-analysis', action='store_true', help='Run full analysis pipeline')

    args = parser.parse_args()

    # Get match data
    matches = []

    if args.file:
        file_path = Path(args.file)
        if file_path.suffix == '.json':
            with open(file_path) as f:
                matches = json.load(f)
        else:
            with open(file_path) as f:
                matches = parse_simple_format(f.read())
    elif args.text:
        matches = parse_simple_format(args.text)
    else:
        matches = input_matches_interactive()

    if not matches:
        logger.error("❌ Inga matcher att lägga till")
        return

    logger.info(f"\n📊 Läser in {len(matches)} matcher för vecka {args.week}/{args.year}")
    for m in matches:
        logger.info(f"  {m['match_number']}. {m['home_team']} - {m['away_team']}")

    # Confirm
    confirm = input("\nFortsätt? (j/n): ").strip().lower()
    if confirm not in ['j', 'ja', 'y', 'yes']:
        logger.info("Avbruten")
        return

    # Create coupon
    db = SessionLocal()
    try:
        coupon = create_coupon_from_manual_input(args.week, args.year, matches, db)

        if args.run_analysis:
            logger.info("\n🔄 Kör analyspipeline...")
            import asyncio

            async def run_analysis():
                # Fetch odds
                logger.info("1/5 Hämtar odds...")
                all_odds = await fetch_all_odds()
                for odds_data in all_odds:
                    bookmaker = odds_data["bookmaker"]
                    for match_odds in odds_data["odds"]:
                        match_number = match_odds["match_number"]
                        match = db.query(Match).filter(
                            Match.coupon_id == coupon.id,
                            Match.match_number == match_number,
                        ).first()
                        if match:
                            odds = Odds(
                                match_id=match.id,
                                bookmaker=bookmaker,
                                home_odds=match_odds["home_odds"],
                                draw_odds=match_odds["draw_odds"],
                                away_odds=match_odds["away_odds"],
                            )
                            odds.calculate_implied_probabilities()
                            db.add(odds)
                db.commit()
                logger.info(f"✓ Fetched odds from {len(all_odds)} bookmakers")

                # Fetch expert predictions
                logger.info("2/5 Hämtar expertprediktioner...")
                all_opinions = await fetch_all_expert_opinions()
                for opinion_data in all_opinions:
                    source = opinion_data["source"]
                    for match_opinion in opinion_data["opinions"]:
                        match_number = match_opinion["match_number"]
                        match = db.query(Match).filter(
                            Match.coupon_id == coupon.id,
                            Match.match_number == match_number,
                        ).first()
                        if match:
                            expert_opinion = ExpertOpinion(
                                match_id=match.id,
                                source=source,
                                expert_name=match_opinion.get("expert_name"),
                                prediction=match_opinion["prediction"],
                                reasoning=match_opinion.get("reasoning"),
                                confidence=match_opinion.get("confidence"),
                            )
                            db.add(expert_opinion)
                db.commit()
                logger.info(f"✓ Fetched opinions from {len(all_opinions)} sources")

                # Calculate value
                logger.info("3/5 Beräknar värde...")
                calculator = ValueCalculator(db)
                analyses = calculator.calculate_all_matches(coupon.id)
                logger.info(f"✓ Calculated value for {len(analyses)} matches")

                # Summarize experts
                logger.info("4/5 Sammanfattar experter...")
                summarizer = ExpertSummarizer(db)
                summaries = summarizer.summarize_all_matches(coupon.id)
                logger.info(f"✓ Summarized opinions for {len(summaries)} matches")

                # Generate rows
                logger.info("5/5 Genererar rader...")
                generator = RowGenerator(db)
                suggested_rows = generator.generate_rows(coupon.id, max_rows=3)
                logger.info(f"✓ Generated {len(suggested_rows)} suggested rows")

            asyncio.run(run_analysis())
            logger.info("✅ Analys klar!")

        logger.info(f"\n✅ Kupong skapad för vecka {args.week}/{args.year}")
        logger.info("Starta webbservern för att se resultatet:")
        logger.info("  python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")

    except Exception as e:
        logger.error(f"❌ Fel: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    main()
