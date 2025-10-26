"""Initialize the database with tables."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.session import init_db


def main() -> None:
    """Create all database tables."""
    print("Creating database tables...")
    init_db()
    print("✓ Database initialized successfully!")


if __name__ == "__main__":
    main()
