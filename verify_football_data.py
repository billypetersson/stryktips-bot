"""Verify loaded football history data."""
from sqlalchemy import create_engine, select, func
from src.config import settings
from src.models.football import Competition, Season, Team, FootballMatch

engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Check competitions
    from sqlalchemy import text
    result = conn.execute(text('SELECT COUNT(*) FROM competitions')).fetchone()
    print(f"Competitions: {result[0]}")

    # Check seasons
    result = conn.execute(text('SELECT COUNT(*) FROM seasons')).fetchone()
    print(f"Seasons: {result[0]}")

    # Check teams
    result = conn.execute(text('SELECT COUNT(*) FROM teams')).fetchone()
    print(f"Teams: {result[0]}")

    # Check matches
    result = conn.execute(text('SELECT COUNT(*) FROM football_matches')).fetchone()
    print(f"Matches: {result[0]}")

    print("\n" + "=" * 60)
    print("SAMPLE DATA")
    print("=" * 60)

    # Show competitions
    result = conn.execute(text('SELECT code, name, country, tier FROM competitions LIMIT 5'))
    print("\nCompetitions:")
    for row in result:
        print(f"  {row[0]}: {row[1]} ({row[2]}, Tier {row[3]})")

    # Show seasons
    result = conn.execute(text('SELECT name, year_start, year_end FROM seasons LIMIT 5'))
    print("\nSeasons:")
    for row in result:
        print(f"  {row[0]} ({row[1]}-{row[2]})")

    # Show teams
    result = conn.execute(text('SELECT name, name_normalized, country FROM teams LIMIT 10'))
    print("\nTeams:")
    for row in result:
        print(f"  {row[0]} → {row[1]} ({row[2]})")

    # Show matches
    result = conn.execute(text('''
        SELECT
            fm.date_utc,
            ht.name as home_team,
            fm.home_score,
            fm.away_score,
            at.name as away_team,
            fm.status
        FROM football_matches fm
        JOIN teams ht ON fm.home_team_id = ht.id
        JOIN teams at ON fm.away_team_id = at.id
        ORDER BY fm.date_utc DESC
        LIMIT 10
    ''')).fetchall()

    print("\nRecent Matches:")
    for row in result:
        from datetime import datetime
        date = row[0]
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        home = row[1]
        away = row[4]
        score = f"{row[2]}-{row[3]}" if row[2] is not None else "vs"
        status = row[5]
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10]
        print(f"  {date_str}: {home} {score} {away} ({status})")
