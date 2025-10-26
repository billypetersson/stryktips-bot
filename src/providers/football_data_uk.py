"""Football-Data.co.uk provider for historical match results and odds.

Free CSV data source with historical results and bookmaker odds.
No API key required.

URL format: https://www.football-data.co.uk/mmz4281/{season}/{division}.csv
Example: https://www.football-data.co.uk/mmz4281/2324/E0.csv (Premier League 2023-24)
"""

import csv
from datetime import datetime
from io import StringIO
from typing import Any

import httpx

from src.providers.base import BaseProvider, MatchData


class FootballDataUKProvider(BaseProvider):
    """Provider for Football-Data.co.uk CSV data."""

    BASE_URL = "https://www.football-data.co.uk/mmz4281"

    # Division codes and names
    COMPETITIONS = {
        "E0": {"name": "Premier League", "country": "England", "tier": 1},
        "E1": {"name": "Championship", "country": "England", "tier": 2},
        "E2": {"name": "League One", "country": "England", "tier": 3},
        "E3": {"name": "League Two", "country": "England", "tier": 4},
        "EC": {"name": "National League", "country": "England", "tier": 5},
        "SC0": {"name": "Scottish Premiership", "country": "Scotland", "tier": 1},
        "SC1": {"name": "Scottish Championship", "country": "Scotland", "tier": 2},
        "SC2": {"name": "Scottish League One", "country": "Scotland", "tier": 3},
        "SC3": {"name": "Scottish League Two", "country": "Scotland", "tier": 4},
    }

    def __init__(self):
        """Initialize Football-Data.co.uk provider."""
        super().__init__("football-data.co.uk")

    async def fetch_competitions(self) -> list[dict[str, Any]]:
        """Fetch available competitions.

        Returns:
            List of competition dicts
        """
        return [
            {
                "code": code,
                "name": info["name"],
                "country": info["country"],
                "tier": info["tier"],
            }
            for code, info in self.COMPETITIONS.items()
        ]

    async def fetch_season_matches(
        self, competition_code: str, season: str
    ) -> list[MatchData]:
        """Fetch all matches for a specific competition season.

        Args:
            competition_code: Division code (e.g., 'E0' for Premier League)
            season: Season in format 'YYYY-YY' (e.g., '2023-24')

        Returns:
            List of MatchData objects
        """
        if competition_code not in self.COMPETITIONS:
            raise ValueError(f"Unknown competition code: {competition_code}")

        # Convert season format: '2023-24' -> '2324'
        season_short = self._convert_season_format(season)

        # Build URL
        url = f"{self.BASE_URL}/{season_short}/{competition_code}.csv"

        # Fetch CSV data
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            csv_content = response.text

        # Parse CSV
        matches = self._parse_csv(csv_content, competition_code, season)
        return matches

    def _convert_season_format(self, season: str) -> str:
        """Convert season format from 'YYYY-YY' to 'YYYY'.

        Args:
            season: Season in format 'YYYY-YY' (e.g., '2023-24')

        Returns:
            Season in format 'YYYY' (e.g., '2324')
        """
        parts = season.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid season format: {season}. Expected 'YYYY-YY'")

        year1 = parts[0][-2:]  # Last 2 digits of first year
        year2 = parts[1]  # Last 2 digits of second year

        return f"{year1}{year2}"

    def _parse_csv(
        self, csv_content: str, competition_code: str, season: str
    ) -> list[MatchData]:
        """Parse CSV content into MatchData objects.

        Args:
            csv_content: Raw CSV content
            competition_code: Division code
            season: Season in format 'YYYY-YY'

        Returns:
            List of MatchData objects
        """
        reader = csv.DictReader(StringIO(csv_content))
        matches = []

        comp_info = self.COMPETITIONS[competition_code]
        year_start, year_end = self._parse_season_years(season)

        for row in reader:
            # Skip rows without essential data
            if not row.get("Date") or not row.get("HomeTeam") or not row.get("AwayTeam"):
                continue

            # Parse date (format can vary: DD/MM/YY or DD/MM/YYYY)
            try:
                date_str = row["Date"].strip()
                if "/" in date_str:
                    parts = date_str.split("/")
                    if len(parts[2]) == 2:  # YY format
                        # Assume 20XX for years 00-99
                        year = 2000 + int(parts[2])
                        date = datetime(year, int(parts[1]), int(parts[0]))
                    else:  # YYYY format
                        date = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                else:
                    continue  # Skip invalid date format
            except (ValueError, IndexError):
                continue  # Skip invalid dates

            # Parse scores
            try:
                home_score = int(row.get("FTHG", "")) if row.get("FTHG") else None
                away_score = int(row.get("FTAG", "")) if row.get("FTAG") else None
            except ValueError:
                home_score = None
                away_score = None

            # Determine status
            status = "finished" if home_score is not None and away_score is not None else "scheduled"

            # Create MatchData
            match = MatchData(
                competition_code=competition_code,
                competition_name=comp_info["name"],
                season_name=season,
                year_start=year_start,
                year_end=year_end,
                home_team_name=row["HomeTeam"].strip(),
                away_team_name=row["AwayTeam"].strip(),
                date=date,
                home_score=home_score,
                away_score=away_score,
                status=status,
                source=self.source_name,
                external_refs={"division": competition_code},
            )

            matches.append(match)

        return matches

    def _parse_season_years(self, season: str) -> tuple[int, int]:
        """Parse season string to extract start and end years.

        Args:
            season: Season in format 'YYYY-YY' (e.g., '2023-24')

        Returns:
            Tuple of (year_start, year_end)
        """
        parts = season.split("-")
        year_start = int(parts[0])
        year_end = int(parts[0][:2] + parts[1])  # 2023-24 -> 2024
        return year_start, year_end
