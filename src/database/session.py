"""Database session management and base configuration."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from src.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    # SQLite specific
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database - create all tables."""
    # Import all models to register them with Base
    from src.models import (  # noqa: F401
        Coupon,
        Match,
        Odds,
        ExpertOpinion,
        Analysis,
        SuggestedRow,
    )

    Base.metadata.create_all(bind=engine)
