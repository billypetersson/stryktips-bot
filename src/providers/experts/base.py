"""Base class for expert prediction providers.

Provides common functionality for scraping expert predictions from various sources,
including rate limiting, HTTP client setup, and data normalization.
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from src.providers.experts.cache import ProviderCache

logger = logging.getLogger(__name__)


@dataclass
class ExpertPrediction:
    """Intermediate representation of an expert prediction before saving to DB."""

    source: str
    author: Optional[str]
    published_at: datetime
    url: str
    match_home_team: Optional[str]  # For matching to our database
    match_away_team: Optional[str]  # For matching to our database
    pick: str  # '1', 'X', '2', '1X', '12', 'X2'
    rationale: Optional[str]
    confidence: Optional[str]
    raw_data: Optional[str]


class BaseExpertProvider(ABC):
    """Base class for all expert prediction providers.

    Provides:
    - Rate limiting to be polite with scraping
    - HTTP client with proper headers
    - Common utilities for parsing
    - Error handling and logging
    """

    def __init__(
        self,
        source_name: str,
        rate_limit_delay: float = 2.0,  # Seconds between requests
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize the provider.

        Args:
            source_name: Name of the source (e.g., "Rekatochklart")
            rate_limit_delay: Minimum seconds between requests
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.source_name = source_name
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self._last_request_time: Optional[float] = None
        self._request_lock = asyncio.Lock()

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        async with self._request_lock:
            if self._last_request_time is not None:
                elapsed = asyncio.get_event_loop().time() - self._last_request_time
                if elapsed < self.rate_limit_delay:
                    wait_time = self.rate_limit_delay - elapsed
                    logger.debug(
                        f"Rate limiting: waiting {wait_time:.2f}s for {self.source_name}"
                    )
                    await asyncio.sleep(wait_time)
            self._last_request_time = asyncio.get_event_loop().time()

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for requests.

        Returns polite, realistic headers to avoid being blocked.
        """
        return {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
            "StryktipsBot/1.0 (+https://github.com/yourusername/stryktips-bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL with rate limiting and retries.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string, or None if all retries failed
        """
        await self._rate_limit()

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=self._get_headers())

                    if response.status_code == 200:
                        html = response.text
                        logger.info(
                            f"Successfully fetched {url} for {self.source_name}"
                        )
                        return html
                    elif response.status_code == 404:
                        logger.warning(
                            f"Page not found (404) for {url} from {self.source_name}"
                        )
                        return None
                    elif response.status_code == 429:
                        # Rate limited - wait longer
                        wait_time = (attempt + 1) * 5
                        logger.warning(
                            f"Rate limited (429) by {self.source_name}, "
                            f"waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(
                            f"HTTP {response.status_code} from {url} "
                            f"(attempt {attempt + 1}/{self.max_retries})"
                        )
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except httpx.TimeoutException:
                logger.warning(
                    f"Timeout fetching {url} from {self.source_name} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(
                    f"Error fetching {url} from {self.source_name}: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(
            f"Failed to fetch {url} from {self.source_name} after {self.max_retries} attempts"
        )
        return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup.

        Args:
            html: HTML content as string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "html.parser")

    def _normalize_team_name(self, name: str) -> str:
        """Normalize team name for matching against database.

        Args:
            name: Raw team name from the source

        Returns:
            Normalized team name
        """
        # Remove extra whitespace
        normalized = " ".join(name.split())

        # Common Swedish abbreviations and variations
        replacements = {
            "IFK": "IFK",
            "AIK": "AIK",
            "BK": "",
            "IF": "",
            "FF": "",
            "FC": "",
        }

        for old, new in replacements.items():
            if name.endswith(f" {old}"):
                normalized = normalized.replace(f" {old}", f" {new}").strip()

        return normalized

    def _parse_pick(self, raw_pick: str) -> Optional[str]:
        """Parse and normalize a pick from raw text.

        Args:
            raw_pick: Raw pick text (e.g., "1", "X", "2", "1X", "Hemma", "Oavgjort", etc.)

        Returns:
            Normalized pick ('1', 'X', '2', '1X', '12', 'X2') or None if invalid
        """
        pick = raw_pick.strip().upper()

        # Direct matches
        if pick in ["1", "X", "2", "1X", "X2", "12"]:
            return pick

        # Swedish terms
        swedish_mapping = {
            "HEMMA": "1",
            "HEMMAVINST": "1",
            "BORTAVINST": "2",
            "BORTA": "2",
            "OAVGJORT": "X",
            "KRYSS": "X",
            "HALVGARDERING": "1X",  # Or could be X2 depending on context
        }

        for swedish, normalized in swedish_mapping.items():
            if swedish in pick:
                return normalized

        logger.warning(f"Could not parse pick: {raw_pick}")
        return None

    def _parse_swedish_date(self, date_str: str) -> Optional[datetime]:
        """Parse Swedish date string to datetime.

        Handles common Swedish date formats like:
        - "26 oktober 2025"
        - "2025-10-26"
        - "Igår" (yesterday)
        - "Idag" (today)

        Args:
            date_str: Date string in Swedish

        Returns:
            Datetime object or None if parsing failed
        """
        if not date_str:
            return datetime.utcnow()

        date_str = date_str.strip()

        # Swedish month names
        swedish_months = {
            'januari': 1, 'jan': 1,
            'februari': 2, 'feb': 2,
            'mars': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'maj': 5,
            'juni': 6, 'jun': 6,
            'juli': 7, 'jul': 7,
            'augusti': 8, 'aug': 8,
            'september': 9, 'sep': 9,
            'oktober': 10, 'okt': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12,
        }

        # Relative dates
        date_lower = date_str.lower()
        if date_lower in ['idag', 'i dag']:
            return datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
        elif date_lower in ['igår', 'i går']:
            return (datetime.utcnow() - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        elif date_lower in ['i förrgår', 'i forgår', 'förrgår']:
            return (datetime.utcnow() - timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)

        # Try ISO format first (2025-10-26)
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

        # Try Swedish format: "26 oktober 2025" or "26 okt 2025"
        # Pattern: day month year
        import re
        pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            day = int(match.group(1))
            month_str = match.group(2).lower()
            year = int(match.group(3))

            month = swedish_months.get(month_str)
            if month:
                try:
                    return datetime(year, month, day, 12, 0, 0)
                except ValueError as e:
                    logger.warning(f"Invalid date components: {day}/{month}/{year}: {e}")

        # Try format: "26/10 2025" or "26/10-2025"
        pattern2 = r'(\d{1,2})[/\-](\d{1,2})[\s\-]*(\d{4})'
        match2 = re.search(pattern2, date_str)
        if match2:
            day = int(match2.group(1))
            month = int(match2.group(2))
            year = int(match2.group(3))
            try:
                return datetime(year, month, day, 12, 0, 0)
            except ValueError as e:
                logger.warning(f"Invalid date: {day}/{month}/{year}: {e}")

        # Try relative days: "För 2 dagar sedan", "3 dagar sedan"
        pattern3 = r'(?:för\s+)?(\d+)\s+dag(?:ar)?\s+sedan'
        match3 = re.search(pattern3, date_lower)
        if match3:
            days_ago = int(match3.group(1))
            return (datetime.utcnow() - timedelta(days=days_ago)).replace(hour=12, minute=0, second=0, microsecond=0)

        # If all parsing fails, return current time
        logger.warning(f"Could not parse Swedish date: '{date_str}', using current time")
        return datetime.utcnow()

    @abstractmethod
    async def fetch_latest_predictions(
        self, max_items: int = 50
    ) -> list[ExpertPrediction]:
        """Fetch the latest expert predictions from this source.

        Args:
            max_items: Maximum number of predictions to fetch

        Returns:
            List of ExpertPrediction objects
        """
        pass

    async def fetch_predictions_for_week(
        self, week_number: int, year: int
    ) -> list[ExpertPrediction]:
        """Fetch predictions for a specific Stryktips week.

        Args:
            week_number: Stryktips week number (1-52)
            year: Year

        Returns:
            List of ExpertPrediction objects for that week
        """
        # Default implementation - can be overridden by subclasses
        logger.info(
            f"Week-specific fetching not implemented for {self.source_name}, "
            f"falling back to latest predictions"
        )
        all_predictions = await self.fetch_latest_predictions(max_items=100)

        # TODO: Filter by date range based on week_number and year
        return all_predictions
