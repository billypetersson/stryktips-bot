"""Service for loading football history data into database."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.football import Competition, Season, Team, FootballMatch
from src.providers.base import MatchData, normalize_team_name


class FootballHistoryService:
    """Service for managing football history data."""

    def __init__(self, session: AsyncSession):
        """Initialize service.

        Args:
            session: Database session
        """
        self.session = session

    async def load_matches(self, matches: list[MatchData]) -> dict[str, int]:
        """Load matches into database.

        Creates competitions, seasons, teams, and matches as needed.
        Uses upsert logic to handle duplicates.

        Args:
            matches: List of MatchData objects from providers

        Returns:
            Dict with counts of created/updated entities
        """
        stats = {
            "competitions": 0,
            "seasons": 0,
            "teams": 0,
            "matches": 0,
            "skipped": 0,
        }

        if not matches:
            return stats

        # Group matches by competition and season
        comp_season_groups: dict[tuple[str, str], list[MatchData]] = {}
        for match in matches:
            key = (match.competition_code, match.season_name)
            if key not in comp_season_groups:
                comp_season_groups[key] = []
            comp_season_groups[key].append(match)

        # Process each competition/season
        for (comp_code, season_name), season_matches in comp_season_groups.items():
            # Get or create competition
            competition = await self._get_or_create_competition(
                season_matches[0]  # Use first match for competition info
            )
            if competition:
                stats["competitions"] += 1

            # Get or create season
            season = await self._get_or_create_season(
                competition, season_matches[0]
            )
            if season:
                stats["seasons"] += 1

            # Process matches for this season
            for match_data in season_matches:
                try:
                    # Get or create teams
                    home_team = await self._get_or_create_team(
                        match_data.home_team_name,
                        match_data.competition_code[:3].upper()  # Extract country code
                    )
                    away_team = await self._get_or_create_team(
                        match_data.away_team_name,
                        match_data.competition_code[:3].upper()
                    )

                    if not home_team or not away_team:
                        stats["skipped"] += 1
                        continue

                    # Create or update match
                    created = await self._upsert_match(
                        season, home_team, away_team, match_data
                    )
                    if created:
                        stats["matches"] += 1

                except Exception as e:
                    print(f"Error processing match: {e}")
                    stats["skipped"] += 1
                    continue

        await self.session.commit()
        return stats

    async def _get_or_create_competition(
        self, match_data: MatchData
    ) -> Competition | None:
        """Get or create competition.

        Args:
            match_data: Match data containing competition info

        Returns:
            Competition object
        """
        # Check if exists
        stmt = select(Competition).where(Competition.code == match_data.competition_code)
        result = await self.session.execute(stmt)
        competition = result.scalar_one_or_none()

        if competition:
            return None  # Already exists, return None to indicate not created

        # Create new
        # Extract country from competition name or code
        country = self._extract_country(match_data.competition_name, match_data.competition_code)

        competition = Competition(
            code=match_data.competition_code,
            name=match_data.competition_name,
            country=country,
            tier=self._guess_tier(match_data.competition_name),
        )

        self.session.add(competition)
        await self.session.flush()  # Get ID
        return competition

    async def _get_or_create_season(
        self, competition: Competition | None, match_data: MatchData
    ) -> Season | None:
        """Get or create season.

        Args:
            competition: Competition object (or None if already exists)
            match_data: Match data containing season info

        Returns:
            Season object
        """
        # Get competition if not provided
        if competition is None:
            stmt = select(Competition).where(Competition.code == match_data.competition_code)
            result = await self.session.execute(stmt)
            competition = result.scalar_one_or_none()

        if not competition:
            return None

        # Check if exists
        stmt = (
            select(Season)
            .where(Season.competition_id == competition.id)
            .where(Season.name == match_data.season_name)
        )
        result = await self.session.execute(stmt)
        season = result.scalar_one_or_none()

        if season:
            return season  # Return existing

        # Create new
        season = Season(
            competition_id=competition.id,
            name=match_data.season_name,
            year_start=match_data.year_start,
            year_end=match_data.year_end,
        )

        self.session.add(season)
        await self.session.flush()  # Get ID
        return season

    async def _get_or_create_team(
        self, team_name: str, country_code: str
    ) -> Team | None:
        """Get or create team.

        Args:
            team_name: Team name
            country_code: Country code (e.g., 'ENG', 'SCO')

        Returns:
            Team object
        """
        # Normalize name
        normalized_name = normalize_team_name(team_name)

        # Check if exists by normalized name
        stmt = select(Team).where(Team.name_normalized == normalized_name)
        result = await self.session.execute(stmt)
        team = result.scalar_one_or_none()

        if team:
            return team

        # Map country code to full name
        country_map = {
            "E": "England",
            "ENG": "England",
            "SC": "Scotland",
            "SCO": "Scotland",
            "W": "Wales",
            "WAL": "Wales",
        }
        country = country_map.get(country_code, "England")

        # Create new
        team = Team(
            name=team_name,
            name_normalized=normalized_name,
            country=country,
        )

        self.session.add(team)
        await self.session.flush()  # Get ID
        return team

    async def _upsert_match(
        self,
        season: Season,
        home_team: Team,
        away_team: Team,
        match_data: MatchData,
    ) -> bool:
        """Create or update match.

        Args:
            season: Season object
            home_team: Home team
            away_team: Away team
            match_data: Match data

        Returns:
            True if created, False if updated
        """
        # Check if match exists (same season, teams, and date within 1 day)
        stmt = (
            select(FootballMatch)
            .where(FootballMatch.season_id == season.id)
            .where(FootballMatch.home_team_id == home_team.id)
            .where(FootballMatch.away_team_id == away_team.id)
            .where(FootballMatch.date_utc >= match_data.date.replace(hour=0, minute=0, second=0))
            .where(FootballMatch.date_utc < match_data.date.replace(hour=23, minute=59, second=59))
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update if new data has scores and existing doesn't
            if match_data.home_score is not None and existing.home_score is None:
                existing.home_score = match_data.home_score
                existing.away_score = match_data.away_score
                existing.status = match_data.status
                existing.source = match_data.source
                existing.source_ts = datetime.utcnow()
            return False

        # Create new match
        match = FootballMatch(
            season_id=season.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            matchday=match_data.matchday,
            date_utc=match_data.date,
            status=match_data.status,
            home_score=match_data.home_score,
            away_score=match_data.away_score,
            external_refs=match_data.external_refs,
            source=match_data.source,
            source_ts=datetime.utcnow(),
        )

        self.session.add(match)
        return True

    def _extract_country(self, competition_name: str, competition_code: str) -> str:
        """Extract country from competition name or code.

        Args:
            competition_name: Competition name
            competition_code: Competition code

        Returns:
            Country name
        """
        # Check code prefix
        if competition_code.startswith("E"):
            return "England"
        elif competition_code.startswith("SC"):
            return "Scotland"
        elif competition_code.startswith("eng"):
            return "England"
        elif competition_code.startswith("sco"):
            return "Scotland"

        # Check name
        name_lower = competition_name.lower()
        if "england" in name_lower or "premier league" in name_lower or "championship" in name_lower:
            return "England"
        elif "scotland" in name_lower or "scottish" in name_lower:
            return "Scotland"

        return "England"  # Default

    def _guess_tier(self, competition_name: str) -> int:
        """Guess competition tier from name.

        Args:
            competition_name: Competition name

        Returns:
            Tier number (1-5)
        """
        name_lower = competition_name.lower()

        if "premier" in name_lower or "premiership" in name_lower:
            return 1
        elif "championship" in name_lower:
            return 2
        elif "league one" in name_lower or "league 1" in name_lower:
            return 3
        elif "league two" in name_lower or "league 2" in name_lower:
            return 4
        elif "national" in name_lower:
            return 5

        return 1  # Default to top tier
