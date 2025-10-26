"""Base scraper class with common functionality."""

from abc import ABC, abstractmethod
from typing import Any
import httpx
from bs4 import BeautifulSoup

from src.config import settings


class BaseScraper(ABC):
    """Base class for all scrapers."""

    def __init__(self) -> None:
        """Initialize scraper with HTTP client."""
        self.timeout = settings.scrape_timeout
        self.headers = {
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
        }

    async def fetch(self, url: str) -> str:
        """Fetch HTML content from URL."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self.headers, follow_redirects=True)
            response.raise_for_status()
            return response.text

    async def fetch_json(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """Fetch JSON content from URL.

        Args:
            url: URL to fetch
            headers: Optional custom headers (overrides default headers)
        """
        request_headers = headers if headers is not None else self.headers
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=request_headers, follow_redirects=True)
            response.raise_for_status()
            return response.json()

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup."""
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    async def scrape(self) -> Any:
        """Main scraping method to be implemented by subclasses."""
        pass
