#!/usr/bin/env python3
"""Script to load football history data from open sources.

Usage:
    python scripts/load_football_history.py --competitions E0,E1 --seasons 2023-24,2022-23
    python scripts/load_football_history.py --all  # Load all available data

Providers:
    - Football-Data.co.uk (CSV) - Free historical data
    - footballcsv (GitHub) - CC0-1.0 open data

Control providers via environment variables:
    ENABLE_FOOTBALL_DATA_UK=true
    ENABLE_FOOTBALLCSV=true
"""

import asyncio
import argparse
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.config import settings
from src.providers.football_data_uk import FootballDataUKProvider
from src.providers.footballcsv import FootballCSVProvider
from src.services.football_history import FootballHistoryService


async def load_data(competitions: list[str], seasons: list[str], provider_names: list[str] | None = None):
    """Load football history data.

    Args:
        competitions: List of competition codes to load
        seasons: List of seasons in format 'YYYY-YY'
        provider_names: Optional list of provider names to use
    """
    print("=" * 60)
    print("FOOTBALL HISTORY DATA LOADER")
    print("=" * 60)
    print(f"Competitions: {', '.join(competitions)}")
    print(f"Seasons: {', '.join(seasons)}")
    print()

    # Initialize providers based on config
    providers = []

    if not provider_names or "football-data-uk" in provider_names:
        if settings.enable_football_data_uk:
            providers.append(FootballDataUKProvider())
            print("✓ Enabled: Football-Data.co.uk (CSV)")

    if not provider_names or "footballcsv" in provider_names:
        if settings.enable_footballcsv:
            providers.append(FootballCSVProvider())
            print("✓ Enabled: footballcsv (GitHub)")

    if not providers:
        print("ERROR: No providers enabled. Check your configuration.")
        return

    print()
    print("-" * 60)

    # Create database connection
    # Convert sync URL to async if needed
    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        db_url = db_url.replace("sqlite:", "sqlite+aiosqlite:")
    elif db_url.startswith("postgresql"):
        db_url = db_url.replace("postgresql:", "postgresql+asyncpg:")

    engine = create_async_engine(db_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    total_stats = {
        "competitions": 0,
        "seasons": 0,
        "teams": 0,
        "matches": 0,
        "skipped": 0,
    }

    # Process each provider
    for provider in providers:
        print(f"\nProcessing provider: {provider.source_name}")
        print("-" * 60)

        provider_stats = {
            "competitions": 0,
            "seasons": 0,
            "teams": 0,
            "matches": 0,
            "skipped": 0,
        }

        # Fetch available competitions from provider
        available_comps = await provider.fetch_competitions()
        available_codes = {comp["code"] for comp in available_comps}

        # Map between different provider codes
        comp_mapping = _get_competition_mapping(provider.source_name)

        for comp_code in competitions:
            # Try to map competition code for this provider
            provider_comp_code = comp_mapping.get(comp_code, comp_code)

            if provider_comp_code not in available_codes:
                print(f"  ⊗ Skipping {comp_code} (not available in {provider.source_name})")
                continue

            for season in seasons:
                try:
                    print(f"  • Fetching {provider_comp_code} {season}...", end=" ", flush=True)

                    # Fetch matches
                    matches = await provider.fetch_season_matches(provider_comp_code, season)

                    if not matches:
                        print("No data")
                        continue

                    print(f"{len(matches)} matches", end=" ", flush=True)

                    # Load into database
                    async with SessionLocal() as session:
                        service = FootballHistoryService(session)
                        stats = await service.load_matches(matches)

                        # Update totals
                        for key in stats:
                            provider_stats[key] += stats[key]
                            total_stats[key] += stats[key]

                        print(
                            f"→ +{stats['matches']} matches, "
                            f"{stats['skipped']} skipped"
                        )

                except Exception as e:
                    print(f"ERROR: {e}")
                    continue

        # Print provider summary
        print()
        print(f"Provider '{provider.source_name}' summary:")
        print(f"  Competitions: {provider_stats['competitions']}")
        print(f"  Seasons: {provider_stats['seasons']}")
        print(f"  Teams: {provider_stats['teams']}")
        print(f"  Matches: {provider_stats['matches']}")
        print(f"  Skipped: {provider_stats['skipped']}")

    # Print total summary
    print()
    print("=" * 60)
    print("TOTAL SUMMARY")
    print("=" * 60)
    print(f"Competitions created: {total_stats['competitions']}")
    print(f"Seasons created: {total_stats['seasons']}")
    print(f"Teams created: {total_stats['teams']}")
    print(f"Matches loaded: {total_stats['matches']}")
    print(f"Matches skipped: {total_stats['skipped']}")
    print()

    await engine.dispose()


def _get_competition_mapping(provider_name: str) -> dict[str, str]:
    """Get competition code mapping for a provider.

    Maps standard codes to provider-specific codes.

    Args:
        provider_name: Provider name

    Returns:
        Dict mapping standard codes to provider codes
    """
    if provider_name == "football-data.co.uk":
        # Football-Data.co.uk uses codes like E0, E1, E2, etc.
        return {
            "premier-league": "E0",
            "championship": "E1",
            "league-one": "E2",
            "league-two": "E3",
        }
    elif provider_name == "footballcsv":
        # footballcsv uses codes like eng.1, eng.2, etc.
        return {
            "premier-league": "eng.1",
            "championship": "eng.2",
            "league-one": "eng.3",
            "league-two": "eng.4",
            "E0": "eng.1",
            "E1": "eng.2",
            "E2": "eng.3",
            "E3": "eng.4",
        }

    return {}


def _get_default_competitions() -> list[str]:
    """Get default competitions to load.

    Returns:
        List of competition codes
    """
    return ["E0", "E1"]  # Premier League and Championship


def _get_default_seasons() -> list[str]:
    """Get default seasons to load (last 3 seasons).

    Returns:
        List of season strings in format 'YYYY-YY'
    """
    current_year = datetime.now().year
    current_month = datetime.now().month

    # If before July, current season is previous year
    if current_month < 7:
        current_year -= 1

    seasons = []
    for i in range(3):  # Last 3 seasons
        year = current_year - i
        season = f"{year}-{str(year + 1)[-2:]}"
        seasons.append(season)

    return seasons


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load football history data from open sources"
    )
    parser.add_argument(
        "--competitions",
        type=str,
        help="Comma-separated list of competition codes (e.g., 'E0,E1')",
    )
    parser.add_argument(
        "--seasons",
        type=str,
        help="Comma-separated list of seasons (e.g., '2023-24,2022-23')",
    )
    parser.add_argument(
        "--providers",
        type=str,
        help="Comma-separated list of providers (e.g., 'football-data-uk,footballcsv')",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Load all available competitions and seasons (last 3 years)",
    )

    args = parser.parse_args()

    # Determine competitions
    if args.competitions:
        competitions = [c.strip() for c in args.competitions.split(",")]
    else:
        competitions = _get_default_competitions()

    # Determine seasons
    if args.seasons:
        seasons = [s.strip() for s in args.seasons.split(",")]
    else:
        seasons = _get_default_seasons()

    # Determine providers
    providers = None
    if args.providers:
        providers = [p.strip() for p in args.providers.split(",")]

    # Load data
    await load_data(competitions, seasons, providers)


if __name__ == "__main__":
    asyncio.run(main())
