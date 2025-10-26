"""Scraper for Svenska Spel - fetches coupon and streckprocent."""

import logging
from datetime import datetime
from typing import Any
from dateutil import parser as date_parser

from src.scrapers.base import BaseScraper
from src.config import settings

logger = logging.getLogger(__name__)


class SvenskaSpelScraper(BaseScraper):
    """Scraper for Svenska Spel Stryktips coupon and distribution data."""

    def __init__(self) -> None:
        """Initialize Svenska Spel scraper."""
        super().__init__()
        self.base_url = settings.svenska_spel_base_url
        self.api_base = "https://api.svenskaspel.se"

    async def scrape(self) -> dict[str, Any]:
        """
        Scrape current Stryktips coupon.

        Tries multiple strategies:
        1. Svenska Spel public API
        2. Web scraping from spela.svenskaspel.se
        3. Fallback to mock data

        Returns a dict with coupon data and matches.
        """
        logger.info("Fetching Stryktips coupon from Svenska Spel")

        # Strategy 1: Try API endpoints
        try:
            coupon_data = await self._fetch_from_api()
            if coupon_data:
                logger.info(
                    f"✓ Fetched coupon from API: week {coupon_data['week_number']} "
                    f"with {len(coupon_data['matches'])} matches"
                )
                return coupon_data
        except Exception as e:
            logger.warning(f"API fetch failed: {e}, trying web scraping...")

        # Strategy 2: Try web scraping
        try:
            coupon_data = await self._fetch_from_web()
            if coupon_data:
                logger.info(
                    f"✓ Fetched coupon from web: week {coupon_data['week_number']} "
                    f"with {len(coupon_data['matches'])} matches"
                )
                return coupon_data
        except Exception as e:
            logger.warning(f"Web scraping failed: {e}, falling back to mock data...")

        # Strategy 3: Fallback to mock data
        logger.warning("⚠️  Using MOCK DATA - real scraping not yet implemented")
        coupon_data = await self._fetch_mock_coupon()

        logger.info(
            f"Fetched coupon for week {coupon_data['week_number']} "
            f"with {len(coupon_data['matches'])} matches"
        )

        return coupon_data

    async def _fetch_from_api(self) -> dict[str, Any] | None:
        """
        Attempt to fetch from Svenska Spel API.

        Uses the working endpoint:
        - https://api.spela.svenskaspel.se/draw/1/stryktipset/draws

        Returns None if no active draws or unsuccessful.
        """
        endpoint = "https://api.spela.svenskaspel.se/draw/1/stryktipset/draws"

        try:
            logger.debug(f"Trying API endpoint: {endpoint}")

            # Use special headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Referer': 'https://spela.svenskaspel.se/stryktipset',
            }

            data = await self.fetch_json(endpoint, headers=headers)

            if data and isinstance(data, dict):
                draws = data.get("draws", [])
                if not draws:
                    logger.warning("API returned no active draws - coupon may not be open yet")
                    return None

                # Get the first (latest) draw
                draw = draws[0]
                return self._parse_api_response(draw)
        except Exception as e:
            logger.debug(f"API fetch failed: {e}")
            return None

        return None

    def _parse_api_response(self, draw: dict[str, Any]) -> dict[str, Any]:
        """
        Parse API draw response into our standard format.

        Expected structure (to be verified with real data):
        {
            "drawNumber": int,
            "drawDate": str (ISO datetime),
            "drawState": str ("open", "closed", etc.),
            "events": [ ... list of matches ... ],
            "distribution": { ... streckprocent ... },
            ...
        }
        """
        # Log the structure for debugging when real data is available
        logger.info(f"Parsing draw with keys: {list(draw.keys())}")

        try:
            # Extract basic coupon info
            # Note: Field names are guesses - may need adjustment with real data
            draw_number = draw.get("drawNumber") or draw.get("drawId") or draw.get("number")
            draw_date_str = draw.get("drawDate") or draw.get("date") or draw.get("drawTime")
            events = draw.get("drawEvents") or draw.get("events") or draw.get("matches") or []

            # Parse draw date
            if draw_date_str:
                draw_date = date_parser.parse(draw_date_str)
            else:
                draw_date = datetime.now()

            # Calculate week number from draw date
            week_number = draw_date.isocalendar()[1]

            # Extract jackpot if available
            jackpot = draw.get("jackpot") or draw.get("estimatedJackpot")
            if jackpot and isinstance(jackpot, dict):
                jackpot_amount = jackpot.get("amount")
            elif isinstance(jackpot, (int, float)):
                jackpot_amount = int(jackpot)
            else:
                jackpot_amount = None

            # Parse matches/events
            matches = []
            for idx, event in enumerate(events, start=1):
                match = self._parse_event(event, idx)
                if match:
                    matches.append(match)

            if not matches:
                logger.warning("No matches found in API response - structure may have changed")
                raise ValueError("No matches found in draw")

            logger.info(f"✓ Successfully parsed draw {draw_number} with {len(matches)} matches")

            return {
                "week_number": week_number,
                "year": draw_date.year,
                "draw_date": draw_date.isoformat(),
                "jackpot_amount": jackpot_amount,
                "matches": matches,
            }

        except Exception as e:
            logger.error(f"Failed to parse API response: {e}")
            logger.debug(f"Draw data: {draw}")
            raise

    def _parse_event(self, event: dict[str, Any], match_number: int) -> dict[str, Any] | None:
        """
        Parse a single event/match from API response.

        Real structure from Svenska Spel API:
        {
            "eventNumber": int,
            "match": {
                "participants": [
                    {"type": "home", "name": str, ...},
                    {"type": "away", "name": str, ...}
                ],
                "matchStart": str (ISO datetime),
                ...
            },
            "svenskaFolket": {
                "one": str (percentage),
                "x": str (percentage),
                "two": str (percentage)
            },
            ...
        }
        """
        try:
            # Extract match data
            match = event.get("match", {})
            participants = match.get("participants", [])

            # Extract team names from participants
            home_team_name = "Unknown"
            away_team_name = "Unknown"

            for participant in participants:
                if participant.get("type") == "home":
                    home_team_name = participant.get("name", "Unknown")
                elif participant.get("type") == "away":
                    away_team_name = participant.get("name", "Unknown")

            # Extract kickoff time
            kickoff_str = match.get("matchStart")
            if kickoff_str:
                kickoff_time = date_parser.parse(kickoff_str).isoformat()
            else:
                kickoff_time = datetime.now().isoformat()

            # Extract distribution (streckprocent) from svenskaFolket
            svenska_folket = event.get("svenskaFolket", {})
            home_pct = svenska_folket.get("one")
            draw_pct = svenska_folket.get("x")
            away_pct = svenska_folket.get("two")

            # Convert to float if string
            def to_float(val):
                if val is None:
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            return {
                "match_number": match_number,
                "home_team": home_team_name,
                "away_team": away_team_name,
                "kickoff_time": kickoff_time,
                "home_percentage": to_float(home_pct),
                "draw_percentage": to_float(draw_pct),
                "away_percentage": to_float(away_pct),
            }

        except Exception as e:
            logger.warning(f"Failed to parse event {match_number}: {e}")
            logger.debug(f"Event data: {event}")
            return None

    async def _fetch_from_web(self) -> dict[str, Any] | None:
        """
        Attempt to scrape from Svenska Spel website using Playwright.

        Main page: https://spela.svenskaspel.se/stryktipset

        Uses Playwright for JavaScript rendering.
        Falls back to None if Playwright not installed or scraping fails.

        Returns None if unsuccessful.
        """
        try:
            from src.scrapers.svenska_spel_playwright import PlaywrightSvenskaSpelScraper

            logger.info("Attempting web scraping with Playwright...")
            playwright_scraper = PlaywrightSvenskaSpelScraper()
            data = await playwright_scraper.scrape()
            return data

        except ImportError:
            logger.warning("Playwright not installed - web scraping not available")
            logger.info("Install with: pip install playwright && playwright install chromium")
            return None
        except Exception as e:
            logger.warning(f"Playwright scraping failed: {e}")
            return None

    async def _fetch_mock_coupon(self) -> dict[str, Any]:
        """
        Generate mock coupon data.

        In production, replace this with actual API calls to Svenska Spel.
        Possible approaches:
        1. Use their public API (if available)
        2. Scrape their website
        3. Use RSS feeds or structured data
        """
        # Calculate current week number
        now = datetime.now()
        week_number = now.isocalendar()[1]

        # Mock matches - typically 13 matches
        matches = []
        for i in range(1, 14):
            matches.append({
                "match_number": i,
                "home_team": f"Hemmalag {i}",
                "away_team": f"Bortalag {i}",
                "kickoff_time": datetime.now().isoformat(),
                # Streckprocent (distribution) - mock values
                "home_percentage": 30.0 + i * 2,
                "draw_percentage": 25.0 + i,
                "away_percentage": 45.0 - i * 3,
            })

        return {
            "week_number": week_number,
            "year": now.year,
            "draw_date": now.isoformat(),
            "jackpot_amount": 10_000_000,  # 10 million SEK
            "matches": matches,
        }

    async def fetch_distribution(self, week_number: int) -> dict[int, dict[str, float]]:
        """
        Fetch streckprocent (distribution) for a specific week.

        Args:
            week_number: Week number to fetch distribution for

        Returns:
            Dict mapping match_number to distribution percentages
        """
        logger.info(f"Fetching distribution for week {week_number}")

        # Mock implementation
        distribution: dict[int, dict[str, float]] = {}
        for i in range(1, 14):
            distribution[i] = {
                "home": 30.0 + i * 2,
                "draw": 25.0 + i,
                "away": 45.0 - i * 3,
            }

        return distribution
