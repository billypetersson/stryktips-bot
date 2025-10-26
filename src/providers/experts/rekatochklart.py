"""Rekatochklart expert prediction provider.

Scrapes expert predictions from https://rekatochklart.se/
One of Sweden's most popular Stryktips blogs.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from src.providers.experts.base import BaseExpertProvider, ExpertPrediction

logger = logging.getLogger(__name__)


class RekatochklartProvider(BaseExpertProvider):
    """Provider for Rekatochklart (https://rekatochklart.se/).

    Rekatochklart is a popular Swedish blog about betting and Stryktips,
    publishing weekly tips and analysis for Swedish football pools.
    """

    BASE_URL = "https://rekatochklart.se"
    STRYKTIPS_CATEGORY = f"{BASE_URL}/category/stryktipset"

    def __init__(self, rate_limit_delay: float = 3.0):
        """Initialize Rekatochklart provider.

        Args:
            rate_limit_delay: Seconds between requests (default: 3s for politeness)
        """
        super().__init__(
            source_name="Rekatochklart",
            rate_limit_delay=rate_limit_delay,
            timeout=30,
            max_retries=3,
        )

    async def fetch_latest_predictions(
        self, max_items: int = 50
    ) -> list[ExpertPrediction]:
        """Fetch latest Stryktips predictions from Rekatochklart.

        Args:
            max_items: Maximum number of articles to fetch

        Returns:
            List of ExpertPrediction objects
        """
        logger.info(f"Fetching latest predictions from {self.source_name}")

        # Fetch the Stryktips category page
        html = await self._fetch_html(self.STRYKTIPS_CATEGORY)
        if not html:
            logger.error(f"Failed to fetch {self.STRYKTIPS_CATEGORY}")
            return []

        soup = self._parse_html(html)
        predictions = []

        # Find all article links on the category page
        article_urls = self._extract_article_urls(soup, max_items)
        logger.info(f"Found {len(article_urls)} articles to process")

        # Fetch and parse each article
        for article_url in article_urls[:max_items]:
            article_predictions = await self._parse_article(article_url)
            predictions.extend(article_predictions)

        logger.info(
            f"Fetched {len(predictions)} predictions from {len(article_urls)} articles"
        )
        return predictions

    def _extract_article_urls(self, soup, max_items: int) -> list[str]:
        """Extract article URLs from the category page.

        Args:
            soup: BeautifulSoup object of the category page
            max_items: Maximum number of URLs to extract

        Returns:
            List of article URLs
        """
        urls = []

        # Look for article links
        # Common WordPress/blog patterns:
        # - Articles in <article> tags with links in <h2> or <h3>
        # - Links with rel="bookmark" or class="entry-title-link"
        articles = soup.find_all("article", limit=max_items * 2)  # Get extra in case

        for article in articles:
            # Try multiple selectors
            link = (
                article.find("a", {"rel": "bookmark"})
                or article.find("a", class_=re.compile("entry-title"))
                or article.find("h2", class_=re.compile("entry-title"))
                and article.find("h2").find("a")
            )

            if link and link.get("href"):
                url = link["href"]
                # Ensure absolute URL
                if not url.startswith("http"):
                    url = self.BASE_URL + url if url.startswith("/") else f"{self.BASE_URL}/{url}"

                # Only include if it looks like a Stryktips article
                if "stryktips" in url.lower() and url not in urls:
                    urls.append(url)

        logger.info(f"Extracted {len(urls)} article URLs from category page")
        return urls

    async def _parse_article(self, url: str) -> list[ExpertPrediction]:
        """Parse a single Rekatochklart article for predictions.

        Args:
            url: Article URL

        Returns:
            List of ExpertPrediction objects from this article
        """
        logger.debug(f"Parsing article: {url}")

        html = await self._fetch_html(url)
        if not html:
            logger.warning(f"Failed to fetch article: {url}")
            return []

        soup = self._parse_html(html)
        predictions = []

        # Extract article metadata
        article_data = self._extract_article_metadata(soup, url)
        if not article_data:
            logger.warning(f"Could not extract metadata from {url}")
            return []

        # Find the match predictions in the article content
        match_predictions = self._extract_match_predictions(soup)

        # Create ExpertPrediction objects
        for match_pred in match_predictions:
            try:
                prediction = ExpertPrediction(
                    source=self.source_name,
                    author=article_data.get("author"),
                    published_at=article_data.get("published_at", datetime.utcnow()),
                    url=url,
                    match_home_team=match_pred.get("home_team"),
                    match_away_team=match_pred.get("away_team"),
                    pick=match_pred["pick"],
                    rationale=match_pred.get("rationale"),
                    confidence=match_pred.get("confidence"),
                    raw_data=match_pred.get("raw_text"),
                )
                predictions.append(prediction)
            except KeyError as e:
                logger.warning(f"Missing required field {e} in match prediction from {url}")
                continue

        logger.debug(f"Extracted {len(predictions)} predictions from {url}")
        return predictions

    def _extract_article_metadata(self, soup, url: str) -> Optional[dict]:
        """Extract metadata from article (author, date, etc.).

        Args:
            soup: BeautifulSoup object of the article
            url: Article URL

        Returns:
            Dictionary with metadata or None if extraction failed
        """
        metadata = {"url": url}

        # Extract author
        # Common selectors: <span class="author">, <a rel="author">, meta tag
        author_elem = (
            soup.find("span", class_=re.compile("author"))
            or soup.find("a", {"rel": "author"})
            or soup.find("meta", {"name": "author"})
        )
        if author_elem:
            metadata["author"] = author_elem.get("content", author_elem.get_text(strip=True))

        # Extract publication date
        # Common selectors: <time>, <meta property="article:published_time">
        date_elem = (
            soup.find("time", {"datetime": True})
            or soup.find("meta", {"property": "article:published_time"})
            or soup.find("span", class_=re.compile("date|time"))
        )

        if date_elem:
            date_str = date_elem.get("datetime") or date_elem.get("content") or date_elem.get_text(strip=True)
            try:
                # Try ISO format first
                metadata["published_at"] = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                # Fall back to Swedish date parsing
                metadata["published_at"] = self._parse_swedish_date(date_str)
        else:
            metadata["published_at"] = datetime.utcnow()

        return metadata

    def _extract_match_predictions(self, soup) -> list[dict]:
        """Extract individual match predictions from article content.

        Args:
            soup: BeautifulSoup object of the article

        Returns:
            List of dictionaries with match prediction data
        """
        predictions = []

        # Find the main content area
        content = (
            soup.find("div", class_=re.compile("entry-content|post-content|article-content"))
            or soup.find("article")
        )

        if not content:
            logger.warning("Could not find article content area")
            return []

        # Look for match predictions in various formats
        # Format 1: Numbered list (1. Liverpool - Aston Villa: 1)
        # Format 2: Table with matches and picks
        # Format 3: Paragraphs with bold match names

        # Try to find structured data first (tables, lists)
        tables = content.find_all("table")
        if tables:
            predictions.extend(self._parse_predictions_from_table(tables[0]))

        lists = content.find_all(["ul", "ol"])
        for list_elem in lists:
            predictions.extend(self._parse_predictions_from_list(list_elem))

        # If no structured data, try parsing from paragraphs
        if not predictions:
            paragraphs = content.find_all("p")
            predictions.extend(self._parse_predictions_from_paragraphs(paragraphs))

        return predictions

    def _parse_predictions_from_table(self, table) -> list[dict]:
        """Parse predictions from an HTML table.

        Args:
            table: BeautifulSoup table element

        Returns:
            List of prediction dictionaries
        """
        predictions = []
        rows = table.find_all("tr")

        for row in rows[1:]:  # Skip header row
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                # Assuming format: Match | Pick | Rationale
                match_text = cells[0].get_text(strip=True)
                pick_text = cells[1].get_text(strip=True)

                parsed = self._parse_match_line(match_text, pick_text)
                if parsed:
                    if len(cells) >= 3:
                        parsed["rationale"] = cells[2].get_text(strip=True)
                    predictions.append(parsed)

        return predictions

    def _parse_predictions_from_list(self, list_elem) -> list[dict]:
        """Parse predictions from an HTML list (ul/ol).

        Args:
            list_elem: BeautifulSoup list element

        Returns:
            List of prediction dictionaries
        """
        predictions = []
        items = list_elem.find_all("li")

        for item in items:
            text = item.get_text(strip=True)
            # Look for patterns like:
            # "1. Liverpool - Aston Villa: 1"
            # "Liverpool - Aston Villa (1)"
            # "Match 1: Liverpool vs Aston Villa - Hemmavinst"

            parsed = self._parse_match_line_combined(text)
            if parsed:
                predictions.append(parsed)

        return predictions

    def _parse_predictions_from_paragraphs(self, paragraphs) -> list[dict]:
        """Parse predictions from paragraph text.

        Args:
            paragraphs: List of BeautifulSoup paragraph elements

        Returns:
            List of prediction dictionaries
        """
        predictions = []

        for para in paragraphs:
            text = para.get_text(strip=True)

            # Look for match patterns
            parsed = self._parse_match_line_combined(text)
            if parsed:
                predictions.append(parsed)

        return predictions

    def _parse_match_line(self, match_text: str, pick_text: str) -> Optional[dict]:
        """Parse a match description and separate pick.

        Args:
            match_text: Text describing the match (e.g., "Liverpool - Aston Villa")
            pick_text: Text with the pick (e.g., "1", "Hemma")

        Returns:
            Dictionary with match data or None
        """
        # Parse teams from match text
        # Common separators: " - ", " vs ", " v "
        team_pattern = r"(.+?)\s+(?:-|vs?\.?|–)\s+(.+)"
        match = re.search(team_pattern, match_text)

        if not match:
            return None

        home_team = self._normalize_team_name(match.group(1))
        away_team = self._normalize_team_name(match.group(2))

        # Parse pick
        pick = self._parse_pick(pick_text)
        if not pick:
            return None

        return {
            "home_team": home_team,
            "away_team": away_team,
            "pick": pick,
            "raw_text": f"{match_text}: {pick_text}",
        }

    def _parse_match_line_combined(self, text: str) -> Optional[dict]:
        """Parse a single line containing both match and pick.

        Args:
            text: Full text line (e.g., "1. Liverpool - Aston Villa: 1")

        Returns:
            Dictionary with match data or None
        """
        # Pattern: optional number, teams with separator, colon/parentheses, pick
        # Examples:
        # "1. Liverpool - Aston Villa: 1"
        # "Liverpool vs Aston Villa (Hemma)"
        # "Match 5: Man City - Arsenal - 1X"

        pattern = r"(?:\d+\.?\s+)?(?:Match\s+\d+:\s+)?(.+?)\s+(?:-|vs?\.?|–)\s+(.+?)(?:\s*[-:()]\s*|\s+)([1X2]{1,2}|\w+)\s*(?:\((.+?)\))?.*"
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            return None

        home_team = self._normalize_team_name(match.group(1))
        away_team = self._normalize_team_name(match.group(2))
        pick_raw = match.group(3)
        rationale = match.group(4) if match.lastindex >= 4 else None

        pick = self._parse_pick(pick_raw)
        if not pick:
            return None

        result = {
            "home_team": home_team,
            "away_team": away_team,
            "pick": pick,
            "raw_text": text,
        }

        if rationale:
            result["rationale"] = rationale

        return result
