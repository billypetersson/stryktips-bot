# Football History Module

This module provides historical football match data from open sources for analysis and predictions.

## Features

- ✅ Normalized database schema with 7 tables (competitions, seasons, teams, venues, matches, events, standings)
- ✅ Multiple data providers with pluggable architecture
- ✅ Automatic deduplication and data merging
- ✅ Full Alembic migration support
- ✅ Async/await support for efficient data loading
- ✅ Team name normalization for consistent matching

## Data Sources

### Enabled by Default (Open Data)

1. **Football-Data.co.uk** (CSV)
   - License: Free to use
   - Coverage: English leagues (Premier League, Championship, League One, League Two)
   - Data: Match results, odds from multiple bookmakers
   - Historical: 20+ years of data
   - API Key: Not required

2. **footballcsv** (GitHub)
   - License: CC0-1.0 (Public Domain)
   - Coverage: Major European leagues
   - Data: Match results, basic stats
   - Repository: https://github.com/footballcsv
   - API Key: Not required

### Optional Sources (Disabled by Default)

3. **FiveThirtyEight Soccer SPI**
   - License: CC BY 4.0
   - Coverage: Global leagues with SPI ratings
   - Data: Match results, team ratings, predictions
   - Repository: https://github.com/fivethirtyeight/data
   - Status: Not implemented yet

4. **Wikipedia/Wikidata**
   - License: CC BY-SA 4.0 (requires attribution)
   - Coverage: Comprehensive historical data
   - Data: Teams, players, seasons, trophies
   - Status: Not implemented yet

## Database Schema

```
competitions
├── id (PK)
├── code (unique)
├── name
├── country
└── tier

seasons
├── id (PK)
├── competition_id (FK)
├── name
├── year_start
└── year_end

teams
├── id (PK)
├── name
├── name_normalized (unique)
├── country
├── founded_year
└── external_refs (JSON)

football_matches
├── id (PK)
├── season_id (FK)
├── home_team_id (FK)
├── away_team_id (FK)
├── venue_id (FK)
├── matchday
├── date_utc
├── status
├── home_score
├── away_score
├── external_refs (JSON)
└── source

football_events
├── id (PK)
├── match_id (FK)
├── team_id (FK)
├── minute
├── type (goal, card, substitution, etc.)
├── player
└── detail (JSON)

football_standings
├── id (PK)
├── season_id (FK)
├── matchday
└── table (JSON)

venues
├── id (PK)
├── name
├── city
├── capacity
└── external_refs (JSON)
```

## Usage

### Load Historical Data

```bash
# Load Premier League 2023-24 season
python scripts/load_football_history.py --competitions E0 --seasons 2023-24

# Load multiple competitions and seasons
python scripts/load_football_history.py \
  --competitions E0,E1 \
  --seasons 2023-24,2022-23,2021-22

# Load with specific providers
python scripts/load_football_history.py \
  --competitions E0 \
  --seasons 2023-24 \
  --providers football-data-uk

# Load default (Premier League + Championship, last 3 seasons)
python scripts/load_football_history.py
```

### Competition Codes

#### Football-Data.co.uk
- `E0` - Premier League
- `E1` - Championship
- `E2` - League One
- `E3` - League Two
- `EC` - National League
- `SC0` - Scottish Premiership
- `SC1` - Scottish Championship

#### footballcsv
- `eng.1` - Premier League
- `eng.2` - Championship
- `eng.3` - League One
- `eng.4` - League Two
- `sco.1` - Scottish Premiership

### Environment Variables

Control which providers are enabled via `.env`:

```bash
# Enable/disable providers
ENABLE_FOOTBALL_DATA_UK=true
ENABLE_FOOTBALLCSV=true
ENABLE_FIVETHIRTYEIGHT=false
ENABLE_WIKIPEDIA=false
```

### Programmatic Usage

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.providers.football_data_uk import FootballDataUKProvider
from src.services.football_history import FootballHistoryService

# Initialize provider
provider = FootballDataUKProvider()

# Fetch matches
matches = await provider.fetch_season_matches("E0", "2023-24")

# Load into database
engine = create_async_engine("sqlite+aiosqlite:///./stryktips.db")
SessionLocal = async_sessionmaker(engine)

async with SessionLocal() as session:
    service = FootballHistoryService(session)
    stats = await service.load_matches(matches)
    print(f"Loaded {stats['matches']} matches")
```

### Query Data

```python
from sqlalchemy import select
from src.models.football import Competition, Season, FootballMatch, Team

# Get all Premier League matches
stmt = (
    select(FootballMatch)
    .join(Season)
    .join(Competition)
    .where(Competition.code == "E0")
    .where(Season.name == "2023-24")
)
matches = await session.execute(stmt)

# Get team's home record
stmt = (
    select(FootballMatch)
    .join(Team, FootballMatch.home_team_id == Team.id)
    .where(Team.name_normalized == "arsenal")
    .where(FootballMatch.status == "finished")
)
home_matches = await session.execute(stmt)
```

## Data Quality

### Team Name Normalization

Team names are automatically normalized to handle variations:
- Lowercase conversion
- Removal of common suffixes (FC, United, City, etc.)
- Special character removal
- Whitespace normalization

Examples:
- "Man City" → "man"
- "Nottingham Forest" → "nottm forest"
- "West Ham United" → "west ham"

### Deduplication

Matches are deduplicated based on:
- Same season
- Same teams (home and away)
- Same date (within 1 day)

When duplicates are found:
- Existing matches are updated if new data has scores and existing doesn't
- Otherwise, existing data is preserved

## Attribution

When using data from these sources, please provide appropriate attribution:

- **Football-Data.co.uk**: Free to use, no attribution required
- **footballcsv**: CC0-1.0, public domain dedication
- **FiveThirtyEight**: CC BY 4.0, requires attribution
- **Wikipedia/Wikidata**: CC BY-SA 4.0, requires attribution and share-alike

## Development

### Adding a New Provider

1. Create provider class in `src/providers/`:

```python
from src.providers.base import BaseProvider, MatchData

class MyProvider(BaseProvider):
    def __init__(self):
        super().__init__("my-provider")

    async def fetch_competitions(self):
        # Return list of available competitions
        pass

    async def fetch_season_matches(self, competition_code, season):
        # Return list of MatchData objects
        pass
```

2. Register in `src/providers/__init__.py`
3. Add configuration in `src/config.py`
4. Update loader script to include new provider

### Running Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## License Compliance

This module is designed to comply with all data source licenses:

- ✅ Uses only open data sources
- ✅ Respects rate limits and ToS
- ✅ Provides attribution mechanisms
- ✅ Supports license requirements (CC0, CC BY, CC BY-SA)
- ✅ No commercial API dependencies

## Future Enhancements

- [ ] FiveThirtyEight SPI provider
- [ ] Wikipedia/Wikidata provider
- [ ] Player statistics
- [ ] Match events (goals, cards, substitutions)
- [ ] League standings tracking
- [ ] Venue information
- [ ] Advanced team statistics
- [ ] Head-to-head records
- [ ] Form analysis (last N matches)
- [ ] REST API endpoints for querying history
