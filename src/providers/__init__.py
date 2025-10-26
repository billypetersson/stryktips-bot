"""Football history data providers."""

from src.providers.base import BaseProvider
from src.providers.football_data_uk import FootballDataUKProvider
from src.providers.footballcsv import FootballCSVProvider

__all__ = [
    "BaseProvider",
    "FootballDataUKProvider",
    "FootballCSVProvider",
]
