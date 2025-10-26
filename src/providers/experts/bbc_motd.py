"""BBC Match of the Day provider.

BBC Match of the Day provides expert analysis and predictions from top pundits
including match previews, analysis, and expert opinions.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from src.providers.experts.base import BaseExpertProvider, ExpertPrediction

logger = logging.getLogger(__name__)


class BBCMatchOfTheDayProvider(BaseExpertProvider):
    """Provider for BBC Match of the Day.

    BBC's Match of the Day features expert analysis from renowned pundits
    including Alan Shearer, Ian Wright, and Gary Lineker.

    Note: This provider fetches articles. Video analysis transcription requires ASR module.
    """

    BASE_URL = "https://www.bbc.com"
    FOOTBALL_URL = f"{BASE_URL}/sport/football"
    MOTD_URL = f"{BASE_URL}/programmes/b006tj0q"

    def __init__(self, rate_limit_delay: float = 3.0):
        """Initialize BBC Match of the Day provider.

        Args:
            rate_limit_delay: Seconds between requests (default: 3s)
        """
        super().__init__(
            source_name="BBC Match of the Day",
            rate_limit_delay=rate_limit_delay,
            timeout=30,
            max_retries=3,
            cache_ttl_hours=12,
        )

    async def fetch_latest_predictions(
        self, max_items: int = 50
    ) -> list[ExpertPrediction]:
        """Fetch latest predictions from BBC Match of the Day.

        Args:
            max_items: Maximum number of articles to fetch

        Returns:
            List of ExpertPrediction objects
        """
        logger.info(f"Fetching latest predictions from {self.source_name}")

        # Fetch the football section
        html = await self._fetch_html(self.FOOTBALL_URL)
        if not html:
            logger.error(f"Failed to fetch {self.FOOTBALL_URL}")
            return []

        soup = self._parse_html(html)
        predictions = []

        # Find article links
        article_urls = self._extract_article_urls(soup, max_items)
        logger.info(f"Found {len(article_urls)} articles")

        # Filter for match prediction content
        prediction_articles = [
            url for url in article_urls
            if any(keyword in url.lower() for keyword in [
                'prediction', 'preview', 'analysis', 'motd', 'match-of-the-day',
                'lawrenson', 'shearer', 'wright'
            ])
        ]

        logger.info(f"Filtered to {len(prediction_articles)} prediction articles")

        for article_url in prediction_articles[:max_items]:
            article_predictions = await self._parse_article(article_url)
            predictions.extend(article_predictions)

        logger.info(
            f"Fetched {len(predictions)} predictions from {len(prediction_articles)} articles"
        )
        return predictions

    def _extract_article_urls(self, soup, max_items: int) -> list[str]:
        """Extract article URLs.

        Args:
            soup: BeautifulSoup object
            max_items: Max articles to extract

        Returns:
            List of article URLs
        """
        urls = []

        # Find all article links
        article_links = soup.find_all(
            "a",
            href=re.compile(r"/sport/football/")
        )

        for link in article_links[:max_items * 2]:
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
            soup.find("h1", class_=re.compile("headline|title"))
            or soup.find("h1")
        )
        title = title_elem.get_text(strip=True) if title_elem else None

        # Extract summary
        summary_elem = (
            soup.find("meta", {"property": "og:description"})
            or soup.find("meta", {"name": "description"})
            or soup.find("p", class_=re.compile("intro|summary"))
        )
        if summary_elem:
            summary = (
                summary_elem.get("content")
                if summary_elem.name == "meta"
                else summary_elem.get_text(strip=True)
            )
        else:
            summary = None

        # Extract author
        author = article_data.get("author", "BBC Match of the Day")

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
                if match_pred.get("league"):
                    match_tags["tournament"] = match_pred["league"]

                prediction = ExpertPrediction(
                    source=self.source_name,
                    author=author,
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

        # Extract author
        author_elem = (
            soup.find("a", {"rel": "author"})
            or soup.find("meta", {"name": "author"})
            or soup.find("span", class_=re.compile("author|byline"))
        )
        if author_elem:
            metadata["author"] = (
                author_elem.get("content")
                if author_elem.name == "meta"
                else author_elem.get_text(strip=True)
            )

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
                metadata["published_at"] = datetime.utcnow()
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
            soup.find("div", class_=re.compile("article|content|story"))
            or soup.find("article")
        )

        if not content:
            logger.warning("Could not find article content")
            return []

        text = content.get_text()

        # BBC format: "Team A v Team B - prediction"
        pattern = r'([A-Z][a-zA-Z\s&]+?)\s+v\s+([A-Z][a-zA-Z\s&]+?)(?:\s*[-:]\s*)(Home win|Away win|Draw|[\dX\-]{1,3})'
        matches = re.finditer(pattern, text)

        for match in matches:
            home_team = match.group(1).strip()
            away_team = match.group(2).strip()
            prediction_text = match.group(3).strip()

            # Convert prediction to pick format
            pick = self._convert_prediction_to_pick(prediction_text)
            if not pick:
                continue

            # Extract rationale
            context_start = match.end()
            context_end = min(context_start + 250, len(text))
            context = text[context_start:context_end]

            sentences = re.split(r'[.!?]\s+', context)
            rationale = sentences[0].strip() if sentences and len(sentences[0]) > 15 else None

            predictions.append({
                "home_team": self._normalize_team_name(home_team),
                "away_team": self._normalize_team_name(away_team),
                "pick": pick,
                "rationale": rationale,
                "confidence": None,
                "league": None,
                "raw_text": match.group(0),
            })

        logger.debug(f"Extracted {len(predictions)} match predictions")
        return predictions

    def _convert_prediction_to_pick(self, prediction: str) -> Optional[str]:
        """Convert prediction text to pick format.

        Args:
            prediction: Prediction text

        Returns:
            Pick ('1', 'X', '2', etc.) or None
        """
        pred_lower = prediction.lower().strip()

        if any(term in pred_lower for term in ['home win', 'home victory']):
            return '1'
        elif any(term in pred_lower for term in ['away win', 'away victory']):
            return '2'
        elif 'draw' in pred_lower:
            return 'X'

        # Try numeric format like "2-1"
        score_match = re.match(r'(\d+)-(\d+)', prediction)
        if score_match:
            home_score = int(score_match.group(1))
            away_score = int(score_match.group(2))

            if home_score > away_score:
                return '1'
            elif away_score > home_score:
                return '2'
            else:
                return 'X'

        return self._parse_pick(prediction)
