"""Stryktipspodden expert prediction provider.

Scrapes episode metadata from Stryktipspodden and optionally extracts predictions
from show notes or transcripts.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from src.providers.experts.base import BaseExpertProvider, ExpertPrediction

logger = logging.getLogger(__name__)


class StryktipsoddenProvider(BaseExpertProvider):
    """Provider for Stryktipspodden podcast.

    Stryktipspodden is a popular Swedish podcast about betting and Stryktips.

    This provider:
    1. Fetches episode metadata from the podcast feed/website
    2. Extracts predictions from show notes if available
    3. Can be extended with ASR transcription for audio analysis
    """

    # Note: URL needs to be verified - this is a placeholder
    BASE_URL = "https://stryktipspodden.se"  # Or RSS feed URL
    RSS_FEED = f"{BASE_URL}/feed"  # Typical WordPress podcast feed

    def __init__(self, rate_limit_delay: float = 3.0, enable_transcription: bool = False):
        """Initialize Stryktipspodden provider.

        Args:
            rate_limit_delay: Seconds between requests
            enable_transcription: Whether to transcribe audio (requires ASR setup)
        """
        super().__init__(
            source_name="Stryktipspodden",
            rate_limit_delay=rate_limit_delay,
            timeout=30,
            max_retries=3,
        )
        self.enable_transcription = enable_transcription

    async def fetch_latest_predictions(
        self, max_items: int = 10
    ) -> list[ExpertPrediction]:
        """Fetch latest predictions from Stryktipspodden.

        Args:
            max_items: Maximum number of episodes to check

        Returns:
            List of ExpertPrediction objects
        """
        logger.info(f"Fetching latest predictions from {self.source_name}")

        # Fetch RSS feed or episode list
        episodes = await self._fetch_latest_episodes(max_items)

        predictions = []
        for episode in episodes:
            episode_predictions = await self._parse_episode(episode)
            predictions.extend(episode_predictions)

        logger.info(
            f"Extracted {len(predictions)} predictions from {len(episodes)} episodes"
        )
        return predictions

    async def _fetch_latest_episodes(self, max_items: int) -> list[dict]:
        """Fetch latest episode metadata.

        Args:
            max_items: Maximum number of episodes to fetch

        Returns:
            List of episode dictionaries
        """
        # Try RSS feed first
        episodes = await self._fetch_from_rss(max_items)

        if not episodes:
            # Fall back to website scraping
            episodes = await self._fetch_from_website(max_items)

        return episodes

    async def _fetch_from_rss(self, max_items: int) -> list[dict]:
        """Fetch episodes from RSS feed.

        Args:
            max_items: Maximum number of episodes

        Returns:
            List of episode dictionaries
        """
        logger.info(f"Fetching RSS feed from {self.RSS_FEED}")

        html = await self._fetch_html(self.RSS_FEED)
        if not html:
            logger.warning("Failed to fetch RSS feed")
            return []

        soup = self._parse_html(html)
        episodes = []

        # Parse RSS/XML feed
        items = soup.find_all("item", limit=max_items)

        for item in items:
            try:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubdate") or item.find("pubDate")
                description_elem = item.find("description") or item.find("itunes:summary")

                if not title_elem or not link_elem:
                    continue

                # Only include Stryktips-related episodes
                title = title_elem.get_text(strip=True)
                if "stryktips" not in title.lower():
                    continue

                episode = {
                    "title": title,
                    "url": link_elem.get_text(strip=True),
                    "description": description_elem.get_text(strip=True) if description_elem else "",
                }

                # Parse publication date
                if pub_date_elem:
                    date_str = pub_date_elem.get_text(strip=True)
                    try:
                        # RSS typically uses RFC 822 format
                        from email.utils import parsedate_to_datetime
                        episode["published_at"] = parsedate_to_datetime(date_str)
                    except Exception as e:
                        logger.warning(f"Could not parse date '{date_str}': {e}")
                        episode["published_at"] = datetime.utcnow()
                else:
                    episode["published_at"] = datetime.utcnow()

                # Look for audio URL (for future transcription)
                enclosure = item.find("enclosure")
                if enclosure and enclosure.get("url"):
                    episode["audio_url"] = enclosure["url"]

                episodes.append(episode)

            except Exception as e:
                logger.warning(f"Error parsing RSS item: {e}")
                continue

        logger.info(f"Fetched {len(episodes)} episodes from RSS feed")
        return episodes

    async def _fetch_from_website(self, max_items: int) -> list[dict]:
        """Fetch episodes from website (fallback if RSS fails).

        Args:
            max_items: Maximum number of episodes

        Returns:
            List of episode dictionaries
        """
        logger.info(f"Fetching episodes from website {self.BASE_URL}")

        html = await self._fetch_html(self.BASE_URL)
        if not html:
            logger.warning("Failed to fetch website")
            return []

        soup = self._parse_html(html)
        episodes = []

        # Look for episode links
        # This depends on the website structure
        episode_links = soup.find_all("a", href=re.compile("episode|avsnitt", re.I), limit=max_items)

        for link in episode_links:
            title = link.get_text(strip=True)
            url = link["href"]

            if not url.startswith("http"):
                url = self.BASE_URL + url if url.startswith("/") else f"{self.BASE_URL}/{url}"

            if "stryktips" in title.lower():
                episodes.append({
                    "title": title,
                    "url": url,
                    "description": "",
                    "published_at": datetime.utcnow(),
                })

        logger.info(f"Fetched {len(episodes)} episodes from website")
        return episodes

    async def _parse_episode(self, episode: dict) -> list[ExpertPrediction]:
        """Parse predictions from a podcast episode.

        Args:
            episode: Episode dictionary with metadata

        Returns:
            List of ExpertPrediction objects
        """
        predictions = []

        # Extract predictions from description/show notes
        if episode.get("description"):
            desc_predictions = self._extract_predictions_from_text(
                episode["description"],
                episode["url"],
                episode.get("published_at", datetime.utcnow())
            )
            predictions.extend(desc_predictions)

        # Fetch full episode page for more details
        if episode.get("url"):
            html = await self._fetch_html(episode["url"])
            if html:
                soup = self._parse_html(html)
                page_predictions = self._extract_predictions_from_page(
                    soup,
                    episode["url"],
                    episode.get("published_at", datetime.utcnow())
                )
                predictions.extend(page_predictions)

        # Future: Transcribe audio if enabled
        if self.enable_transcription and episode.get("audio_url"):
            # TODO: Implement ASR transcription
            logger.info(f"Transcription enabled but not yet implemented for {episode['title']}")

        return predictions

    def _extract_predictions_from_text(
        self, text: str, url: str, published_at: datetime
    ) -> list[ExpertPrediction]:
        """Extract predictions from plain text (show notes, description).

        Args:
            text: Text to parse
            url: Source URL
            published_at: Publication datetime

        Returns:
            List of ExpertPrediction objects
        """
        predictions = []
        lines = text.split("\n")

        for line in lines:
            parsed = self._parse_match_line_combined(line.strip())
            if parsed:
                try:
                    prediction = ExpertPrediction(
                        source=self.source_name,
                        author=None,  # Podcast hosts could be extracted from metadata
                        published_at=published_at,
                        url=url,
                        match_home_team=parsed["home_team"],
                        match_away_team=parsed["away_team"],
                        pick=parsed["pick"],
                        rationale=parsed.get("rationale"),
                        confidence=None,
                        raw_data=parsed["raw_text"],
                    )
                    predictions.append(prediction)
                except KeyError as e:
                    logger.warning(f"Missing field {e} in parsed prediction")

        return predictions

    def _extract_predictions_from_page(
        self, soup, url: str, published_at: datetime
    ) -> list[ExpertPrediction]:
        """Extract predictions from episode page.

        Args:
            soup: BeautifulSoup object of episode page
            url: Page URL
            published_at: Publication datetime

        Returns:
            List of ExpertPrediction objects
        """
        predictions = []

        # Find the main content
        content = (
            soup.find("div", class_=re.compile("content|entry|episode"))
            or soup.find("article")
        )

        if not content:
            return predictions

        # Extract from various structures
        lists = content.find_all(["ul", "ol"])
        for list_elem in lists:
            items = list_elem.find_all("li")
            for item in items:
                text = item.get_text(strip=True)
                parsed = self._parse_match_line_combined(text)
                if parsed:
                    try:
                        prediction = ExpertPrediction(
                            source=self.source_name,
                            author=None,
                            published_at=published_at,
                            url=url,
                            match_home_team=parsed["home_team"],
                            match_away_team=parsed["away_team"],
                            pick=parsed["pick"],
                            rationale=parsed.get("rationale"),
                            confidence=None,
                            raw_data=parsed["raw_text"],
                        )
                        predictions.append(prediction)
                    except KeyError:
                        continue

        return predictions

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
