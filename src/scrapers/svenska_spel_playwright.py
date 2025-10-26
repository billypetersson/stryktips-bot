"""
Playwright-based scraper for Svenska Spel Stryktips.

This is an EXAMPLE implementation showing how to scrape with browser automation.

Installation required:
    pip install playwright
    playwright install chromium

To use this scraper instead of mock data:
    1. Install dependencies above
    2. Update src/scrapers/svenska_spel.py to use this class
    3. Test with: python -m src.jobs.update_coupon
"""

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class PlaywrightSvenskaSpelScraper:
    """Scraper using Playwright for browser automation."""

    def __init__(self) -> None:
        """Initialize Playwright scraper."""
        self.url = "https://spela.svenskaspel.se/stryktipset"

    async def scrape(self) -> dict[str, Any]:
        """
        Scrape Stryktips coupon using Playwright.

        Returns dict with coupon data and matches.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )

        logger.info(f"Starting Playwright scraper for: {self.url}")

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,  # Set to False for debugging
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            try:
                page = await browser.new_page()

                # Navigate to Stryktips page
                logger.info("Loading Svenska Spel Stryktips page...")
                await page.goto(self.url, wait_until='networkidle', timeout=30000)

                # Wait for matches to load
                # NOTE: These selectors are EXAMPLES and need to be updated
                # based on actual HTML structure from Svenska Spel
                logger.info("Waiting for match data to load...")
                await page.wait_for_selector('[data-testid="match-row"]', timeout=10000)

                # Extract coupon information
                coupon_info = await self._extract_coupon_info(page)

                # Extract all matches
                matches = await self._extract_matches(page)

                logger.info(f"✓ Successfully scraped {len(matches)} matches")

                return {
                    "week_number": coupon_info["week_number"],
                    "year": coupon_info["year"],
                    "draw_date": coupon_info["draw_date"],
                    "jackpot_amount": coupon_info.get("jackpot_amount"),
                    "matches": matches,
                }

            finally:
                await browser.close()

    async def _extract_coupon_info(self, page: Any) -> dict[str, Any]:
        """
        Extract coupon-level information.

        NOTE: Selectors need to be updated based on actual Svenska Spel HTML.
        """
        # Example selectors - MUST BE UPDATED!
        try:
            # Try to find week number
            week_text = await page.text_content('[data-testid="week-number"]')
            week_number = int(week_text.split()[-1]) if week_text else datetime.now().isocalendar()[1]
        except:
            week_number = datetime.now().isocalendar()[1]

        try:
            # Try to find jackpot
            jackpot_text = await page.text_content('[data-testid="jackpot"]')
            # Parse "10 000 000 kr" -> 10000000
            jackpot_amount = int(''.join(filter(str.isdigit, jackpot_text or '0')))
        except:
            jackpot_amount = None

        # Draw date - usually upcoming Saturday
        now = datetime.now()
        days_until_saturday = (5 - now.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        draw_date = datetime(now.year, now.month, now.day) + timedelta(days=days_until_saturday)

        return {
            "week_number": week_number,
            "year": now.year,
            "draw_date": draw_date.isoformat(),
            "jackpot_amount": jackpot_amount,
        }

    async def _extract_matches(self, page: Any) -> list[dict[str, Any]]:
        """
        Extract all match data from the page.

        NOTE: Selectors need to be updated based on actual Svenska Spel HTML.
        """
        # Example JavaScript to extract matches
        # This MUST be updated to match Svenska Spel's actual HTML structure
        matches = await page.evaluate("""
            () => {
                // EXAMPLE CODE - UPDATE SELECTORS!
                const matchRows = document.querySelectorAll('[data-testid="match-row"]');

                return Array.from(matchRows).map((row, index) => {
                    const homeTeam = row.querySelector('.home-team')?.textContent || 'Unknown';
                    const awayTeam = row.querySelector('.away-team')?.textContent || 'Unknown';
                    const kickoff = row.querySelector('.kickoff-time')?.textContent || '';

                    // Streckprocent (distribution percentages)
                    const homePercent = row.querySelector('.percent-home')?.textContent || '0';
                    const drawPercent = row.querySelector('.percent-draw')?.textContent || '0';
                    const awayPercent = row.querySelector('.percent-away')?.textContent || '0';

                    return {
                        match_number: index + 1,
                        home_team: homeTeam.trim(),
                        away_team: awayTeam.trim(),
                        kickoff_time: kickoff.trim(),
                        home_percentage: parseFloat(homePercent) || 33.3,
                        draw_percentage: parseFloat(drawPercent) || 33.3,
                        away_percentage: parseFloat(awayPercent) || 33.3,
                    };
                });
            }
        """)

        # If we couldn't extract real data, log warning
        if not matches or len(matches) == 0:
            logger.warning("Could not extract matches - selectors may be incorrect!")
            logger.warning("Please inspect the HTML and update the selectors in this file.")
            raise ValueError("No matches found - check HTML selectors")

        return matches


# Helper function to test the scraper
async def test_scraper():
    """Test function to run the scraper manually."""
    scraper = PlaywrightSvenskaSpelScraper()
    data = await scraper.scrape()

    print("\n" + "="*60)
    print(f"Week: {data['week_number']}/{data['year']}")
    print(f"Matches: {len(data['matches'])}")
    print("="*60)

    for match in data['matches']:
        print(f"\n{match['match_number']}. {match['home_team']} - {match['away_team']}")
        print(f"   Streck: 1={match['home_percentage']:.0f}% X={match['draw_percentage']:.0f}% 2={match['away_percentage']:.0f}%")


if __name__ == "__main__":
    import asyncio
    from datetime import timedelta

    # Run test
    asyncio.run(test_scraper())
