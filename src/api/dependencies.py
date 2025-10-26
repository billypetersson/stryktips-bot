"""FastAPI dependencies."""

from typing import Generator
from sqlalchemy.orm import Session

from src.database.session import get_db

# Re-export for convenience
__all__ = ["get_db"]
