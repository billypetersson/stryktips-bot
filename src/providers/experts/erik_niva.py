"""Erik Niva expert prediction provider.

Erik Niva is one of Sweden's most respected football analysts,
writing for Sportbladet/Aftonbladet. He provides in-depth Stryktips analysis.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from src.providers.experts.base import BaseExpertProvider, ExpertPrediction

logger = logging.getLogger(__name__)


class ErikNivaProvider(BaseExpertProvider):
    """Provider for Erik Niva's Stryktips columns in Sportbladet.

    Erik Niva is a renowned football analyst who publishes weekly
    Stryktips analysis on Sportbladet/Aftonbladet.
    """

    BASE_URL = "https://www.aftonbladet.se"
    SEARCH_URL = f"{BASE_URL}/author/erik-niva"
    AUTHOR_NAME = "Erik Niva"

    def __init__(self, rate_limit_delay: float = 3.0):
        """Initialize Erik Niva provider.

        Args:
            rate_limit_delay: Seconds between requests (default: 3s)
        """
        super().__init__(
            source_name="Erik Niva",
            rate_limit_delay=rate_limit_delay,
            timeout=30,
            max_retries=3,
            cache_ttl_hours=6,
        )

    async def fetch_latest_predictions(
        self, max_items: int = 50
    ) -> list[ExpertPrediction]:
        """Fetch latest Stryktips predictions from Erik Niva.

        Args:
            max_items: Maximum number of articles to fetch

        Returns:
            List of ExpertPrediction objects
        """
        logger.info(f"Fetching latest predictions from {self.source_name}")

        # Fetch the author page
        html = await self._fetch_html(self.SEARCH_URL)
        if not html:
            logger.error(f"Failed to fetch {self.SEARCH_URL}")
            return []

        soup = self._parse_html(html)
        predictions = []

        # Find article links
        article_urls = self._extract_article_urls(soup, max_items)
        logger.info(f"Found {len(article_urls)} articles from {self.AUTHOR_NAME}")

        # Filter for Stryktips articles and parse each
        stryktips_articles = [
            url for url in article_urls
            if any(keyword in url.lower() for keyword in ['stryktips', 'tips', 'kupong'])
        ]

        logger.info(f"Filtered to {len(stryktips_articles)} Stryktips articles")

        for article_url in stryktips_articles[:max_items]:
            article_predictions = await self._parse_article(article_url)
            predictions.extend(article_predictions)

        logger.info(
            f"Fetched {len(predictions)} predictions from {len(stryktips_articles)} articles"
        )
        return predictions

    def _extract_article_urls(self, soup, max_items: int) -> list[str]:
        """Extract article URLs from the author page.

        Args:
            soup: BeautifulSoup object
            max_items: Max articles to extract

        Returns:
            List of article URLs
        """
        urls = []

        # Find article cards/links
        # Aftonbladet uses <a> tags with class containing "article" or similar
        article_links = soup.find_all("a", href=re.compile(r"/sportbladet/.*"))

        for link in article_links[:max_items * 2]:  # Get extra to filter later
            href = link.get("href")
            if not href:
                continue

            # Ensure full URL
            if href.startswith("/"):
                href = self.BASE_URL + href

            if href not in urls:
                urls.append(href)

        logger.debug(f"Extracted {len(urls)} article URLs")
        return urls[:max_items]

    async def _parse_article(self, url: str) -> list[ExpertPrediction]:
        """Parse an article and extract predictions.

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

        # Extract article metadata
        article_data = self._extract_article_metadata(soup, url)
        if not article_data:
            logger.warning(f"Failed to extract metadata from {url}")
            return []

        # Extract title
        title_elem = (
            soup.find("h1", class_=re.compile("article-title|heading"))
            or soup.find("h1")
        )
        title = title_elem.get_text(strip=True) if title_elem else None

        # Extract summary/excerpt
        summary_elem = (
            soup.find("p", class_=re.compile("preamble|excerpt|lead"))
            or soup.find("meta", {"property": "og:description"})
        )
        if summary_elem:
            summary = (
                summary_elem.get("content")
                if summary_elem.name == "meta"
                else summary_elem.get_text(strip=True)
            )
        else:
            summary = None

        # Extract match predictions
        match_predictions = self._extract_match_predictions(soup)

        if not match_predictions:
            logger.debug(f"No predictions found in {url}")
            return []

        # Create ExpertPrediction objects
        predictions = []
        for match_pred in match_predictions:
            try:
                # Build match_tags
                match_tags = {}
                if match_pred.get("home_team") and match_pred.get("away_team"):
                    match_tags["teams"] = [match_pred["home_team"], match_pred["away_team"]]

                prediction = ExpertPrediction(
                    source=self.source_name,
                    author=self.AUTHOR_NAME,
                    published_at=article_data.get("published_at", datetime.utcnow()),
                    url=url,
                    title=title,
                    summary=summary,
                    match_home_team=match_pred.get("home_team"),
                    match_away_team=match_pred.get("away_team"),
                    pick=match_pred["pick"],
                    rationale=match_pred.get("rationale"),
                    confidence=match_pred.get("confidence"),
                    match_tags=match_tags if match_tags else None,
                    raw_data=match_pred.get("raw_text"),
                )
                predictions.append(prediction)
            except KeyError as e:
                logger.warning(f"Missing required field {e} in match prediction from {url}")
                continue

        logger.debug(f"Extracted {len(predictions)} predictions from {url}")
        return predictions

    def _extract_article_metadata(self, soup, url: str) -> Optional[dict]:
        """Extract metadata from article.

        Args:
            soup: BeautifulSoup object
            url: Article URL

        Returns:
            Dictionary with metadata
        """
        metadata = {"url": url}

        # Extract publication date
        date_elem = (
            soup.find("time", {"datetime": True})
            or soup.find("meta", {"property": "article:published_time"})
        )

        if date_elem:
            date_str = date_elem.get("datetime") or date_elem.get("content")
            try:
                metadata["published_at"] = datetime.fromisoformat(
                    date_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                metadata["published_at"] = self._parse_swedish_date(date_str)
        else:
            metadata["published_at"] = datetime.utcnow()

        return metadata

    def _extract_match_predictions(self, soup) -> list[dict]:
        """Extract match predictions from article.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of prediction dictionaries
        """
        predictions = []

        # Find content area
        content = (
            soup.find("div", class_=re.compile("article-content|article-body"))
            or soup.find("article")
        )

        if not content:
            logger.warning("Could not find article content")
            return []

        # Look for structured match data
        # Common patterns: "1. Team A - Team B: 1" or "Team A - Team B: 1X"
        text = content.get_text()

        # Pattern: Match number, teams, pick
        # Example: "1. Liverpool - Arsenal: 1"
        pattern = r'(\d{1,2})\.?\s*([A-ZÅÄÖ][a-zåäö\s]+?)\s*[-–]\s*([A-ZÅÄÖ][a-zåäö\s]+?):\s*([1X2]{1,2})'
        matches = re.finditer(pattern, text)

        for match in matches:
            match_num = match.group(1)
            home_team = match.group(2).strip()
            away_team = match.group(3).strip()
            pick = match.group(4)

            # Normalize pick
            normalized_pick = self._parse_pick(pick)
            if not normalized_pick:
                continue

            # Try to find rationale (next few sentences)
            context_start = match.end()
            context_end = min(context_start + 200, len(text))
            rationale = text[context_start:context_end].split(".")[0].strip()

            predictions.append({
                "home_team": self._normalize_team_name(home_team),
                "away_team": self._normalize_team_name(away_team),
                "pick": normalized_pick,
                "rationale": rationale if rationale else None,
                "confidence": None,
                "raw_text": match.group(0),
            })

        logger.debug(f"Extracted {len(predictions)} match predictions")
        return predictions
