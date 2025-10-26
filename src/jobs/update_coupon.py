"""Job to update coupon data - run by K8s CronJob."""

import sys
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# Add src to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import settings
from src.database.session import SessionLocal, init_db
from src.models import Coupon, Match, Odds, ExpertOpinion
from src.scrapers.svenska_spel import SvenskaSpelScraper
from src.scrapers.odds_providers import fetch_all_odds
from src.scrapers.experts import fetch_all_expert_opinions
from src.analysis.value_calculator import ValueCalculator
from src.analysis.expert_summarizer import ExpertSummarizer
from src.analysis.row_generator import RowGenerator

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def update_coupon_data(db: Session | None = None) -> Coupon:
    """
    Main job to update coupon data.

    1. Scrape coupon from Svenska Spel
    2. Fetch odds from all providers
    3. Fetch expert opinions
    4. Calculate value
    5. Generate suggested rows

    Args:
        db: Database session (if None, creates new one)

    Returns:
        Updated Coupon object
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        logger.info("=== Starting coupon update ===")

        # 1. Scrape coupon
        logger.info("Step 1: Fetching coupon from Svenska Spel")
        scraper = SvenskaSpelScraper()
        coupon_data = await scraper.scrape()

        # Deactivate old coupons
        db.query(Coupon).filter(Coupon.is_active == True).update(
            {"is_active": False}
        )

        # Create new coupon
        coupon = Coupon(
            week_number=coupon_data["week_number"],
            year=coupon_data["year"],
            draw_date=datetime.fromisoformat(coupon_data["draw_date"]),
            jackpot_amount=coupon_data.get("jackpot_amount"),
            is_active=True,
        )
        db.add(coupon)
        db.flush()  # Get coupon.id

        # Create matches
        for match_data in coupon_data["matches"]:
            match = Match(
                coupon_id=coupon.id,
                match_number=match_data["match_number"],
                home_team=match_data["home_team"],
                away_team=match_data["away_team"],
                kickoff_time=datetime.fromisoformat(match_data["kickoff_time"]),
                home_percentage=match_data.get("home_percentage"),
                draw_percentage=match_data.get("draw_percentage"),
                away_percentage=match_data.get("away_percentage"),
            )
            db.add(match)

        db.commit()
        logger.info(f"✓ Created coupon {coupon.week_number}/{coupon.year} with {len(coupon_data['matches'])} matches")

        # 2. Fetch odds
        logger.info("Step 2: Fetching odds from bookmakers")
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

        # 3. Fetch expert opinions
        logger.info("Step 3: Fetching expert opinions")
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

        # 4. Calculate value
        logger.info("Step 4: Calculating value for all matches")
        calculator = ValueCalculator(db)
        analyses = calculator.calculate_all_matches(coupon.id)
        logger.info(f"✓ Calculated value for {len(analyses)} matches")

        # 5. Summarize expert opinions
        logger.info("Step 5: Summarizing expert opinions")
        summarizer = ExpertSummarizer(db)
        summaries = summarizer.summarize_all_matches(coupon.id)
        logger.info(f"✓ Summarized opinions for {len(summaries)} matches")

        # 6. Generate suggested rows
        logger.info("Step 6: Generating suggested rows")
        generator = RowGenerator(db)
        suggested_rows = generator.generate_rows(coupon.id, max_rows=3)
        logger.info(f"✓ Generated {len(suggested_rows)} suggested rows")

        logger.info("=== Coupon update completed successfully ===")

        return coupon

    finally:
        if should_close:
            db.close()


def main() -> None:
    """Main entry point for CronJob."""
    import asyncio

    # Initialize database
    init_db()

    # Run update
    asyncio.run(update_coupon_data())


if __name__ == "__main__":
    main()
