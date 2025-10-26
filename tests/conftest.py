"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.database.session import Base
from src.config import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Test settings with SQLite in-memory database."""
    return Settings(
        database_url="sqlite:///:memory:",
        debug=True,
        log_level="DEBUG",
    )


@pytest.fixture(scope="function")
def db_session(settings: Settings) -> Session:
    """Create a test database session."""
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
