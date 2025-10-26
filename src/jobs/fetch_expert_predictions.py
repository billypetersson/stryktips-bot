"""Job to fetch expert predictions - run by K8s CronJob or manually.

This job fetches expert predictions from all configured sources and saves them
to the database for use in consensus calculation.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import settings
from src.database.session import async_session_maker, init_db
from src.services.expert_consensus import ExpertConsensusService

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def fetch_expert_predictions_job(max_items_per_source: int = 20) -> dict[str, int]:
    """
    Main job to fetch expert predictions from all sources.

    Args:
        max_items_per_source: Maximum articles/episodes to fetch per source

    Returns:
        Dictionary with counts per source: {source_name: count}
    """
    logger.info("Starting expert predictions fetch job")

    # Initialize database
    init_db()

    # Create async session
    async with async_session_maker() as db:
        try:
            # Create expert consensus service
            service = ExpertConsensusService(db)

            # Fetch and save predictions from all sources
            logger.info(f"Fetching from {len(service.providers)} providers")
            counts = await service.fetch_and_save_latest_predictions(max_items_per_source)

            # Log results
            total = sum(counts.values())
            logger.info(f"✅ Successfully fetched {total} predictions total")
            for source, count in counts.items():
                logger.info(f"  - {source}: {count} predictions")

            return counts

        except Exception as e:
            logger.error(f"❌ Error in expert predictions fetch job: {e}", exc_info=True)
            raise


async def cleanup_old_predictions(days_to_keep: int = 30):
    """
    Clean up old expert predictions from database.

    Args:
        days_to_keep: Number of days to keep predictions (default: 30)
    """
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from src.models.expert_item import ExpertItem

    logger.info(f"Starting cleanup of predictions older than {days_to_keep} days")

    async with async_session_maker() as db:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Delete old predictions
            result = await db.execute(
                delete(ExpertItem).where(ExpertItem.published_at < cutoff_date)
            )
            await db.commit()

            deleted_count = result.rowcount
            logger.info(f"✅ Cleaned up {deleted_count} old predictions")

            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
            await db.rollback()
            raise


def main():
    """
    Main entry point for the job.

    Can be run manually: python -m src.jobs.fetch_expert_predictions
    """
    logger.info("=" * 60)
    logger.info("EXPERT PREDICTIONS FETCH JOB")
    logger.info("=" * 60)

    try:
        # Fetch predictions
        counts = asyncio.run(fetch_expert_predictions_job(max_items_per_source=20))

        # Cleanup old predictions (optional, run weekly)
        # asyncio.run(cleanup_old_predictions(days_to_keep=30))

        logger.info("=" * 60)
        logger.info("JOB COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        logger.info("=" * 60)
        logger.info("JOB FAILED")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
