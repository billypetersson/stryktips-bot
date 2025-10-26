"""Scrapers for various odds providers."""

import logging
from typing import Any
import random

from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class OddsProviderScraper(BaseScraper):
    """Base class for odds provider scrapers."""

    def __init__(self, provider_name: str) -> None:
        """Initialize odds provider scraper."""
        super().__init__()
        self.provider_name = provider_name

    async def scrape(self) -> dict[str, Any]:
        """Scrape odds for all matches."""
        logger.info(f"Fetching odds from {self.provider_name}")
        return await self._fetch_mock_odds()

    async def _fetch_mock_odds(self) -> dict[str, Any]:
        """
        Generate mock odds data.

        In production, replace with actual API calls to bookmakers.

        Options:
        1. Official APIs (if available and you have API keys)
        2. Odds comparison sites APIs (e.g., The Odds API)
        3. Web scraping (check terms of service!)
        """
        odds_data = []
        for i in range(1, 14):
            # Generate realistic odds with some randomness
            base_home = 2.0 + random.uniform(-0.5, 0.5)
            base_draw = 3.5 + random.uniform(-0.5, 0.5)
            base_away = 3.0 + random.uniform(-0.5, 0.5)

            odds_data.append({
                "match_number": i,
                "home_odds": round(base_home, 2),
                "draw_odds": round(base_draw, 2),
                "away_odds": round(base_away, 2),
            })

        return {
            "bookmaker": self.provider_name,
            "odds": odds_data,
        }


class Bet365Scraper(OddsProviderScraper):
    """Scraper for Bet365 odds."""

    def __init__(self) -> None:
        """Initialize Bet365 scraper."""
        super().__init__("Bet365")


class UnibetScraper(OddsProviderScraper):
    """Scraper for Unibet odds."""

    def __init__(self) -> None:
        """Initialize Unibet scraper."""
        super().__init__("Unibet")


class BetssonScraper(OddsProviderScraper):
    """Scraper for Betsson odds."""

    def __init__(self) -> None:
        """Initialize Betsson scraper."""
        super().__init__("Betsson")


async def fetch_all_odds() -> list[dict[str, Any]]:
    """
    Fetch odds from all available providers.

    Returns:
        List of odds data from each provider
    """
    scrapers = [
        Bet365Scraper(),
        UnibetScraper(),
        BetssonScraper(),
    ]

    all_odds = []
    for scraper in scrapers:
        try:
            odds = await scraper.scrape()
            all_odds.append(odds)
        except Exception as e:
            logger.error(f"Failed to fetch odds from {scraper.provider_name}: {e}")

    return all_odds
