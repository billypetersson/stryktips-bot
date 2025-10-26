"""Generic blog provider for Swedish betting blogs.

A configurable provider that can scrape predictions from various Swedish betting
blogs and websites with similar structures.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from src.providers.experts.base import BaseExpertProvider, ExpertPrediction

logger = logging.getLogger(__name__)


class GenericBlogProvider(BaseExpertProvider):
    """Configurable provider for blog-style betting prediction websites.

    Can be configured with different URLs and selectors to scrape various
    Swedish betting blogs that follow common blog patterns.
    """

    def __init__(
        self,
        source_name: str,
        base_url: str,
        stryktips_url: str,
        rate_limit_delay: float = 3.0,
    ):
        """Initialize generic blog provider.

        Args:
            source_name: Name of the source (e.g., "Expressen")
            base_url: Base URL of the website
            stryktips_url: URL for Stryktips section/category
            rate_limit_delay: Seconds between requests
        """
        super().__init__(
            source_name=source_name,
            rate_limit_delay=rate_limit_delay,
            timeout=30,
            max_retries=3,
        )
        self.base_url = base_url
        self.stryktips_url = stryktips_url

    async def fetch_latest_predictions(
        self, max_items: int = 50
    ) -> list[ExpertPrediction]:
        """Fetch latest Stryktips predictions.

        Args:
            max_items: Maximum number of articles to check

        Returns:
            List of ExpertPrediction objects
        """
        logger.info(f"Fetching latest predictions from {self.source_name}")

        # Fetch the Stryktips section/category page
        html = await self._fetch_html(self.stryktips_url)
        if not html:
            logger.error(f"Failed to fetch {self.stryktips_url}")
            return []

        soup = self._parse_html(html)
        predictions = []

        # Find article links
        article_urls = self._extract_article_urls(soup, max_items)
        logger.info(f"Found {len(article_urls)} articles from {self.source_name}")

        # Parse each article
        for article_url in article_urls[:max_items]:
            article_predictions = await self._parse_article(article_url)
            predictions.extend(article_predictions)

        logger.info(
            f"Extracted {len(predictions)} predictions from {len(article_urls)} articles"
        )
        return predictions

    def _extract_article_urls(self, soup, max_items: int) -> list[str]:
        """Extract article URLs from category page.

        Args:
            soup: BeautifulSoup object
            max_items: Maximum URLs to extract

        Returns:
            List of article URLs
        """
        urls = []

        # Try multiple common patterns
        patterns = [
            soup.find_all("article", limit=max_items * 2),
            soup.find_all("div", class_=re.compile("post|article"), limit=max_items * 2),
        ]

        for articles in patterns:
            if not articles:
                continue

            for article in articles:
                link = (
                    article.find("a", {"rel": "bookmark"})
                    or article.find("a", class_=re.compile("title|headline"))
                    or article.find("h2", class_=re.compile("title|headline")).find("a") if article.find("h2") else None
                    or article.find("a", href=True)
                )

                if link and link.get("href"):
                    url = link["href"]

                    # Ensure absolute URL
                    if not url.startswith("http"):
                        url = self.base_url + url if url.startswith("/") else f"{self.base_url}/{url}"

                    # Filter for Stryktips articles
                    if "stryktips" in url.lower() and url not in urls:
                        urls.append(url)

            if urls:  # Stop if we found some URLs
                break

        logger.info(f"Extracted {len(urls)} article URLs")
        return urls

    async def _parse_article(self, url: str) -> list[ExpertPrediction]:
        """Parse a single article for predictions.

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
        predictions = []

        # Extract metadata
        article_data = self._extract_article_metadata(soup, url)
        if not article_data:
            logger.warning(f"Could not extract metadata from {url}")
            return []

        # Extract predictions
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
                logger.warning(f"Missing required field {e} in prediction from {url}")
                continue

        logger.debug(f"Extracted {len(predictions)} predictions from {url}")
        return predictions

    def _extract_article_metadata(self, soup, url: str) -> Optional[dict]:
        """Extract article metadata."""
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
            or soup.find("span", class_=re.compile("date|published"))
        )

        if date_elem:
            date_str = date_elem.get("datetime") or date_elem.get("content") or date_elem.get_text(strip=True)
            try:
                metadata["published_at"] = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                metadata["published_at"] = self._parse_swedish_date(date_str)
        else:
            metadata["published_at"] = datetime.utcnow()

        return metadata

    def _extract_match_predictions(self, soup) -> list[dict]:
        """Extract match predictions from article content."""
        predictions = []

        # Find main content
        content = (
            soup.find("div", class_=re.compile("entry-content|post-content|article-content|article-body"))
            or soup.find("article")
        )

        if not content:
            logger.warning("Could not find article content")
            return []

        # Try structured formats
        tables = content.find_all("table")
        for table in tables:
            predictions.extend(self._parse_predictions_from_table(table))

        lists = content.find_all(["ul", "ol"])
        for list_elem in lists:
            predictions.extend(self._parse_predictions_from_list(list_elem))

        # Try paragraphs if no structured data
        if not predictions:
            paragraphs = content.find_all("p")
            predictions.extend(self._parse_predictions_from_paragraphs(paragraphs))

        return predictions

    def _parse_predictions_from_table(self, table) -> list[dict]:
        """Parse predictions from table."""
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

    def _parse_predictions_from_list(self, list_elem) -> list[dict]:
        """Parse predictions from list."""
        predictions = []
        items = list_elem.find_all("li")

        for item in items:
            text = item.get_text(strip=True)
            parsed = self._parse_match_line_combined(text)
            if parsed:
                predictions.append(parsed)

        return predictions

    def _parse_predictions_from_paragraphs(self, paragraphs) -> list[dict]:
        """Parse predictions from paragraphs."""
        predictions = []

        for para in paragraphs:
            text = para.get_text(strip=True)
            parsed = self._parse_match_line_combined(text)
            if parsed:
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
        """Parse line with both match and pick."""
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


# Pre-configured instances for common sources
class ExpressenProvider(GenericBlogProvider):
    """Provider for Expressen Tips & Odds."""

    def __init__(self, rate_limit_delay: float = 3.0):
        super().__init__(
            source_name="Expressen",
            base_url="https://www.expressen.se",
            stryktips_url="https://www.expressen.se/sport/tips-odds/stryktipset",
            rate_limit_delay=rate_limit_delay,
        )


class TipsmedossProvider(GenericBlogProvider):
    """Provider for Tipsmedoss blog."""

    def __init__(self, rate_limit_delay: float = 3.0):
        super().__init__(
            source_name="Tipsmedoss",
            base_url="https://tipsmedoss.se",  # URL needs verification
            stryktips_url="https://tipsmedoss.se/category/stryktipset",
            rate_limit_delay=rate_limit_delay,
        )


class SpelbloggareProvider(GenericBlogProvider):
    """Provider for Spelbloggare blogs.

    Note: Spelbloggare is a platform with multiple bloggers.
    This provider targets the main Stryktips section.
    """

    def __init__(self, rate_limit_delay: float = 3.0):
        super().__init__(
            source_name="Spelbloggare",
            base_url="https://www.spelbloggare.se",  # URL needs verification
            stryktips_url="https://www.spelbloggare.se/stryktipset",
            rate_limit_delay=rate_limit_delay,
        )
