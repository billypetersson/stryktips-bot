"""FootballCSV provider for open football data from GitHub.

Open football data in CSV format (CC0-1.0 license).
Data source: https://github.com/footballcsv

Repository structure:
- england: https://github.com/footballcsv/england
- scotland: https://github.com/footballcsv/scotland
- etc.

URL format: https://raw.githubusercontent.com/footballcsv/{country}/master/{season}/{league}.csv
Example: https://raw.githubusercontent.com/footballcsv/england/master/2023-24/eng.1.csv
"""

import csv
from datetime import datetime
from io import StringIO
from typing import Any

import httpx

from src.providers.base import BaseProvider, MatchData


class FootballCSVProvider(BaseProvider):
    """Provider for FootballCSV GitHub data."""

    BASE_URL = "https://raw.githubusercontent.com/footballcsv"

    # Competition configurations
    COMPETITIONS = {
        "eng.1": {
            "name": "Premier League",
            "country": "England",
            "tier": 1,
            "repo": "england",
        },
        "eng.2": {
            "name": "Championship",
            "country": "England",
            "tier": 2,
            "repo": "england",
        },
        "eng.3": {
            "name": "League One",
            "country": "England",
            "tier": 3,
            "repo": "england",
        },
        "eng.4": {
            "name": "League Two",
            "country": "England",
            "tier": 4,
            "repo": "england",
        },
        "sco.1": {
            "name": "Scottish Premiership",
            "country": "Scotland",
            "tier": 1,
            "repo": "scotland",
        },
    }

    def __init__(self):
        """Initialize FootballCSV provider."""
        super().__init__("footballcsv")

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
            competition_code: League code (e.g., 'eng.1' for Premier League)
            season: Season in format 'YYYY-YY' (e.g., '2023-24')

        Returns:
            List of MatchData objects
        """
        if competition_code not in self.COMPETITIONS:
            raise ValueError(f"Unknown competition code: {competition_code}")

        comp_info = self.COMPETITIONS[competition_code]

        # Build URL
        url = f"{self.BASE_URL}/{comp_info['repo']}/master/{season}/{competition_code}.csv"

        # Fetch CSV data
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                csv_content = response.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Try alternative branch (main instead of master)
                    url = f"{self.BASE_URL}/{comp_info['repo']}/main/{season}/{competition_code}.csv"
                    response = await client.get(url)
                    response.raise_for_status()
                    csv_content = response.text
                else:
                    raise

        # Parse CSV
        matches = self._parse_csv(csv_content, competition_code, season)
        return matches

    def _parse_csv(
        self, csv_content: str, competition_code: str, season: str
    ) -> list[MatchData]:
        """Parse CSV content into MatchData objects.

        FootballCSV format typically has columns:
        - Round, Date, Team 1, FT, Team 2
        Or:
        - Matchday, Date, Time, Home, Score, Away

        Args:
            csv_content: Raw CSV content
            competition_code: League code
            season: Season in format 'YYYY-YY'

        Returns:
            List of MatchData objects
        """
        reader = csv.DictReader(StringIO(csv_content))
        matches = []

        comp_info = self.COMPETITIONS[competition_code]
        year_start, year_end = self._parse_season_years(season)

        for row in reader:
            # Try to parse different CSV formats
            try:
                match = self._parse_row(row, competition_code, comp_info, season, year_start, year_end)
                if match:
                    matches.append(match)
            except Exception:
                # Skip rows that can't be parsed
                continue

        return matches

    def _parse_row(
        self,
        row: dict[str, str],
        competition_code: str,
        comp_info: dict[str, Any],
        season: str,
        year_start: int,
        year_end: int,
    ) -> MatchData | None:
        """Parse a single CSV row into MatchData.

        Args:
            row: CSV row as dict
            competition_code: League code
            comp_info: Competition info dict
            season: Season string
            year_start: Season start year
            year_end: Season end year

        Returns:
            MatchData object or None if row can't be parsed
        """
        # Try to identify column names (case-insensitive)
        row_lower = {k.lower().strip(): v for k, v in row.items()}

        # Extract date
        date_str = (
            row_lower.get("date")
            or row_lower.get("datum")
            or row_lower.get("match date")
            or ""
        )
        if not date_str:
            return None

        # Parse date (common formats: YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY)
        date = self._parse_date(date_str, year_start, year_end)
        if not date:
            return None

        # Extract teams
        home_team = (
            row_lower.get("home")
            or row_lower.get("team 1")
            or row_lower.get("home team")
            or ""
        ).strip()

        away_team = (
            row_lower.get("away")
            or row_lower.get("team 2")
            or row_lower.get("away team")
            or ""
        ).strip()

        if not home_team or not away_team:
            return None

        # Extract scores
        score_str = (
            row_lower.get("score")
            or row_lower.get("ft")
            or row_lower.get("result")
            or ""
        ).strip()

        home_score, away_score = self._parse_score(score_str)

        # Extract matchday/round
        matchday_str = (
            row_lower.get("round")
            or row_lower.get("matchday")
            or row_lower.get("md")
            or ""
        )
        try:
            matchday = int(matchday_str) if matchday_str else None
        except ValueError:
            matchday = None

        # Determine status
        status = "finished" if home_score is not None and away_score is not None else "scheduled"

        return MatchData(
            competition_code=competition_code,
            competition_name=comp_info["name"],
            season_name=season,
            year_start=year_start,
            year_end=year_end,
            home_team_name=home_team,
            away_team_name=away_team,
            date=date,
            matchday=matchday,
            home_score=home_score,
            away_score=away_score,
            status=status,
            source=self.source_name,
            external_refs={"league": competition_code},
        )

    def _parse_date(self, date_str: str, year_start: int, year_end: int) -> datetime | None:
        """Parse date string to datetime.

        Args:
            date_str: Date string in various formats
            year_start: Season start year (for context)
            year_end: Season end year (for context)

        Returns:
            datetime object or None
        """
        date_str = date_str.strip()

        # Try different date formats
        formats = [
            "%Y-%m-%d",  # 2024-01-15
            "%d.%m.%Y",  # 15.01.2024
            "%d/%m/%Y",  # 15/01/2024
            "%d-%m-%Y",  # 15-01-2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_score(self, score_str: str) -> tuple[int | None, int | None]:
        """Parse score string to home and away scores.

        Args:
            score_str: Score string (e.g., '2-1', '3:0', '1 - 2')

        Returns:
            Tuple of (home_score, away_score)
        """
        if not score_str:
            return None, None

        # Remove spaces
        score_str = score_str.replace(" ", "")

        # Try different separators
        for sep in ["-", ":", "–", "—"]:
            if sep in score_str:
                parts = score_str.split(sep)
                if len(parts) == 2:
                    try:
                        home_score = int(parts[0])
                        away_score = int(parts[1])
                        return home_score, away_score
                    except ValueError:
                        pass

        return None, None

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
