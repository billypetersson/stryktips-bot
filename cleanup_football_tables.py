"""Drop all football tables and reset alembic version."""
from sqlalchemy import create_engine, text
from src.config import settings

engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Drop tables in reverse order (respecting foreign keys)
    tables = [
        'football_events',
        'football_standings',
        'football_matches',
        'seasons',
        'venues',
        'teams',
        'competitions'
    ]

    for table in tables:
        try:
            conn.execute(text(f'DROP TABLE IF EXISTS {table}'))
            print(f"Dropped table: {table}")
        except Exception as e:
            print(f"Error dropping {table}: {e}")

    # Reset alembic version
    try:
        conn.execute(text('DELETE FROM alembic_version'))
        print("Reset alembic_version")
    except Exception as e:
        print(f"Error resetting alembic_version: {e}")

    conn.commit()

print("Cleanup complete!")
