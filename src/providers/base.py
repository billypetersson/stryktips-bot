"""Base provider interface for football history data sources."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


def normalize_team_name(name: str) -> str:
    """Normalize team name for consistent matching.

    Args:
        name: Original team name

    Returns:
        Normalized team name (lowercase, no special chars)
    """
    # Convert to lowercase
    normalized = name.lower()

    # Remove common suffixes
    normalized = re.sub(r"\s+(fc|afc|united|city|town|rovers|wanderers|athletic)$", "", normalized)

    # Remove special characters but keep spaces
    normalized = re.sub(r"[^a-z0-9\s]", "", normalized)

    # Remove extra spaces
    normalized = " ".join(normalized.split())

    return normalized.strip()


@dataclass
class MatchData:
    """Standardized match data from any provider."""

    # Competition & Season
    competition_code: str
    competition_name: str
    season_name: str
    year_start: int
    year_end: int

    # Teams
    home_team_name: str
    away_team_name: str

    # Match details
    date: datetime
    matchday: int | None = None
    home_score: int | None = None
    away_score: int | None = None
    status: str = "finished"

    # Venue (optional)
    venue_name: str | None = None
    venue_city: str | None = None

    # Metadata
    source: str = ""
    external_refs: dict[str, Any] | None = None


@dataclass
class TeamData:
    """Standardized team data from any provider."""

    name: str
    name_normalized: str
    country: str | None = None
    founded_year: int | None = None
    external_refs: dict[str, Any] | None = None


class BaseProvider(ABC):
    """Base class for all football history data providers."""

    def __init__(self, source_name: str):
        """Initialize provider.

        Args:
            source_name: Identifier for this data source
        """
        self.source_name = source_name

    @abstractmethod
    async def fetch_competitions(self) -> list[dict[str, Any]]:
        """Fetch available competitions.

        Returns:
            List of competition dicts with keys: code, name, country, tier
        """
        pass

    @abstractmethod
    async def fetch_season_matches(
        self, competition_code: str, season: str
    ) -> list[MatchData]:
        """Fetch all matches for a specific competition season.

        Args:
            competition_code: Competition identifier (e.g., 'E0' for Premier League)
            season: Season identifier (e.g., '2023-24')

        Returns:
            List of MatchData objects
        """
        pass
