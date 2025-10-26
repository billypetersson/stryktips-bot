"""Verify football history database schema."""
from sqlalchemy import create_engine, inspect, text
from src.config import settings

engine = create_engine(settings.database_url)
inspector = inspect(engine)

print("=" * 60)
print("FOOTBALL HISTORY TABLES")
print("=" * 60)

# Expected tables
expected_tables = [
    'competitions',
    'seasons',
    'teams',
    'venues',
    'football_matches',
    'football_events',
    'football_standings'
]

for table_name in expected_tables:
    if table_name in inspector.get_table_names():
        print(f"\n✓ Table: {table_name}")

        # Show columns
        columns = inspector.get_columns(table_name)
        print(f"  Columns ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"    - {col['name']}: {col['type']} {nullable}")

        # Show indexes
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print(f"  Indexes ({len(indexes)}):")
            for idx in indexes:
                unique = " (UNIQUE)" if idx['unique'] else ""
                print(f"    - {idx['name']}: {idx['column_names']}{unique}")

        # Show foreign keys
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            print(f"  Foreign Keys ({len(fks)}):")
            for fk in fks:
                print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    else:
        print(f"\n✗ Table missing: {table_name}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)

# Check alembic version
with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version')).fetchone()
    if result:
        print(f"\nCurrent migration version: {result[0]}")
