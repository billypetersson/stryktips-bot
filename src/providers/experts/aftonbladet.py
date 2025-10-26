"""Aftonbladet Sportbladet expert prediction provider.

Scrapes expert predictions from Aftonbladet's Sportbladet section.
IMPORTANT: Respects paywall - only extracts publicly available content.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from src.providers.experts.base import BaseExpertProvider, ExpertPrediction

logger = logging.getLogger(__name__)


class AftonbladetProvider(BaseExpertProvider):
    """Provider for Aftonbladet Sportbladet (https://www.aftonbladet.se/sportbladet/).

    Aftonbladet is Sweden's largest tabloid newspaper. Their Sportbladet section
    publishes Stryktips tips and analysis.

    IMPORTANT: This provider respects Aftonbladet's paywall. It only extracts:
    - Article titles and metadata (publicly available)
    - Article URLs for attribution
    - Free preview text (if available)
    - Will NOT attempt to bypass or circumvent paywalled content
    """

    BASE_URL = "https://www.aftonbladet.se"
    STRYKTIPS_URL = f"{BASE_URL}/sportbladet/spel/stryktipset"

    def __init__(self, rate_limit_delay: float = 3.0):
        """Initialize Aftonbladet provider.

        Args:
            rate_limit_delay: Seconds between requests (default: 3s for politeness)
        """
        super().__init__(
            source_name="Aftonbladet",
            rate_limit_delay=rate_limit_delay,
            timeout=30,
            max_retries=3,
        )

    async def fetch_latest_predictions(
        self, max_items: int = 50
    ) -> list[ExpertPrediction]:
        """Fetch latest Stryktips predictions from Aftonbladet.

        Only extracts publicly available content, respects paywall.

        Args:
            max_items: Maximum number of articles to check

        Returns:
            List of ExpertPrediction objects
        """
        logger.info(
            f"Fetching latest predictions from {self.source_name} "
            "(respecting paywall, public content only)"
        )

        # Fetch the Stryktips section page
        html = await self._fetch_html(self.STRYKTIPS_URL)
        if not html:
            logger.error(f"Failed to fetch {self.STRYKTIPS_URL}")
            return []

        soup = self._parse_html(html)
        predictions = []

        # Find article links
        article_urls = self._extract_article_urls(soup, max_items)
        logger.info(f"Found {len(article_urls)} articles to check")

        # Check each article
        for article_url in article_urls[:max_items]:
            article_predictions = await self._parse_article(article_url)
            predictions.extend(article_predictions)

        logger.info(
            f"Extracted {len(predictions)} predictions from {len(article_urls)} articles"
        )
        return predictions

    def _extract_article_urls(self, soup, max_items: int) -> list[str]:
        """Extract article URLs from the Stryktips section page.

        Args:
            soup: BeautifulSoup object of the section page
            max_items: Maximum number of URLs to extract

        Returns:
            List of article URLs
        """
        urls = []

        # Aftonbladet typically uses article tags with links
        articles = soup.find_all("article", limit=max_items * 2)

        for article in articles:
            # Look for main article link
            link = article.find("a", {"href": True})

            if link:
                url = link["href"]

                # Ensure absolute URL
                if not url.startswith("http"):
                    url = self.BASE_URL + url if url.startswith("/") else f"{self.BASE_URL}/{url}"

                # Only include Stryktips articles
                if "stryktips" in url.lower() and url not in urls:
                    urls.append(url)

        logger.info(f"Extracted {len(urls)} article URLs")
        return urls

    async def _parse_article(self, url: str) -> list[ExpertPrediction]:
        """Parse a single Aftonbladet article for predictions.

        Respects paywall - only extracts publicly available content.

        Args:
            url: Article URL

        Returns:
            List of ExpertPrediction objects
        """
        logger.debug(f"Parsing article: {url}")

        html = await self._fetch_html(url)
        if not html:
            logger.warning(f"Failed to fetch article: {url}")
            return []

        soup = self._parse_html(html)

        # Check for paywall
        if self._is_paywalled(soup):
            logger.info(f"Article is paywalled, skipping content extraction: {url}")
            # We can still extract metadata and URL for tracking purposes
            # but won't extract predictions
            return []

        predictions = []

        # Extract article metadata
        article_data = self._extract_article_metadata(soup, url)
        if not article_data:
            logger.warning(f"Could not extract metadata from {url}")
            return []

        # Extract match predictions from publicly available content
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

    def _is_paywalled(self, soup) -> bool:
        """Check if an article is behind a paywall.

        Args:
            soup: BeautifulSoup object of the article

        Returns:
            True if paywalled, False if public
        """
        # Look for common paywall indicators
        paywall_indicators = [
            soup.find(class_=re.compile("paywall|premium|plus", re.I)),
            soup.find(attrs={"data-paywall": True}),
            soup.find(text=re.compile("Aftonbladet Plus|Logga in|Prenumerera", re.I)),
        ]

        is_paywalled = any(indicator for indicator in paywall_indicators)

        if is_paywalled:
            logger.debug("Paywall detected in article")

        return is_paywalled

    def _extract_article_metadata(self, soup, url: str) -> Optional[dict]:
        """Extract metadata from article.

        Args:
            soup: BeautifulSoup object
            url: Article URL

        Returns:
            Dictionary with metadata
        """
        metadata = {"url": url}

        # Extract author
        author_elem = (
            soup.find("span", class_=re.compile("author|byline"))
            or soup.find("a", {"rel": "author"})
            or soup.find("meta", {"name": "author"})
        )
        if author_elem:
            metadata["author"] = author_elem.get("content", author_elem.get_text(strip=True))

        # Extract publication date
        date_elem = (
            soup.find("time", {"datetime": True})
            or soup.find("meta", {"property": "article:published_time"})
        )

        if date_elem:
            date_str = date_elem.get("datetime") or date_elem.get("content")
            try:
                metadata["published_at"] = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                metadata["published_at"] = self._parse_swedish_date(date_str)
        else:
            metadata["published_at"] = datetime.utcnow()

        return metadata

    def _extract_match_predictions(self, soup) -> list[dict]:
        """Extract match predictions from publicly available article content.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of prediction dictionaries
        """
        predictions = []

        # Find the article content (not behind paywall)
        content = (
            soup.find("div", class_=re.compile("article-body|article-content"))
            or soup.find("article")
        )

        if not content:
            logger.warning("Could not find article content")
            return []

        # Look for structured predictions
        # Aftonbladet might use custom components for betting tips
        tip_sections = content.find_all(class_=re.compile("tip|betting|prediction"))

        for section in tip_sections:
            predictions.extend(self._parse_tip_section(section))

        # Also try standard formats (lists, tables)
        lists = content.find_all(["ul", "ol"])
        for list_elem in lists:
            predictions.extend(self._parse_predictions_from_list(list_elem))

        tables = content.find_all("table")
        for table in tables:
            predictions.extend(self._parse_predictions_from_table(table))

        return predictions

    def _parse_tip_section(self, section) -> list[dict]:
        """Parse a betting tip section.

        Args:
            section: BeautifulSoup element containing tips

        Returns:
            List of prediction dictionaries
        """
        predictions = []
        text = section.get_text(strip=True)

        # Look for match patterns in the text
        # Common format: "Liverpool - Aston Villa: 1"
        lines = text.split("\n")
        for line in lines:
            parsed = self._parse_match_line_combined(line.strip())
            if parsed:
                predictions.append(parsed)

        return predictions

    def _parse_predictions_from_list(self, list_elem) -> list[dict]:
        """Parse predictions from HTML list."""
        predictions = []
        items = list_elem.find_all("li")

        for item in items:
            text = item.get_text(strip=True)
            parsed = self._parse_match_line_combined(text)
            if parsed:
                predictions.append(parsed)

        return predictions

    def _parse_predictions_from_table(self, table) -> list[dict]:
        """Parse predictions from HTML table."""
        predictions = []
        rows = table.find_all("tr")

        for row in rows[1:]:  # Skip header
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                match_text = cells[0].get_text(strip=True)
                pick_text = cells[1].get_text(strip=True)

                parsed = self._parse_match_line(match_text, pick_text)
                if parsed:
                    if len(cells) >= 3:
                        parsed["rationale"] = cells[2].get_text(strip=True)
                    predictions.append(parsed)

        return predictions

    def _parse_match_line(self, match_text: str, pick_text: str) -> Optional[dict]:
        """Parse separated match and pick text."""
        team_pattern = r"(.+?)\s+(?:-|vs?\.?|–)\s+(.+)"
        match = re.search(team_pattern, match_text)

        if not match:
            return None

        home_team = self._normalize_team_name(match.group(1))
        away_team = self._normalize_team_name(match.group(2))

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
        """Parse a line with both match and pick."""
        pattern = r"(?:\d+\.?\s+)?(.+?)\s+(?:-|vs?\.?|–)\s+(.+?)(?:\s*[-:]\s*|\s+)([1X2]{1,2}|\w+)"
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            return None

        home_team = self._normalize_team_name(match.group(1))
        away_team = self._normalize_team_name(match.group(2))
        pick_raw = match.group(3)

        pick = self._parse_pick(pick_raw)
        if not pick:
            return None

        return {
            "home_team": home_team,
            "away_team": away_team,
            "pick": pick,
            "raw_text": text,
        }
