"""Application configuration using Pydantic settings."""

from typing import Literal
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Stryktips Bot", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )

    # Database
    database_url: str = Field(
        default="sqlite:///./stryktips.db",
        alias="DATABASE_URL",
        description="Database connection URL",
    )

    # Scrapers
    svenska_spel_base_url: str = Field(
        default="https://www.svenskaspel.se",
        alias="SVENSKA_SPEL_BASE_URL",
    )
    scrape_timeout: int = Field(default=30, alias="SCRAPE_TIMEOUT")
    user_agent: str = Field(
        default="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        alias="USER_AGENT",
    )

    # Odds providers (optional API keys)
    bet365_api_key: str | None = Field(default=None, alias="BET365_API_KEY")
    unibet_api_key: str | None = Field(default=None, alias="UNIBET_API_KEY")
    betsson_api_key: str | None = Field(default=None, alias="BETSSON_API_KEY")

    # Analysis settings
    max_half_covers: int = Field(
        default=2,
        alias="MAX_HALF_COVERS",
        description="Maximum number of half covers (helgarderingar)",
    )
    min_value_threshold: float = Field(
        default=1.05,
        alias="MIN_VALUE_THRESHOLD",
        description="Minimum value threshold for suggesting a sign",
    )

    # Cron
    cron_schedule: str = Field(
        default="0 7 * * 5",
        alias="CRON_SCHEDULE",
        description="Cron schedule for K8s CronJob",
    )

    # Football History Data Providers
    enable_football_data_uk: bool = Field(
        default=True,
        alias="ENABLE_FOOTBALL_DATA_UK",
        description="Enable Football-Data.co.uk provider (free CSV)",
    )
    enable_footballcsv: bool = Field(
        default=True,
        alias="ENABLE_FOOTBALLCSV",
        description="Enable footballcsv GitHub provider (CC0-1.0)",
    )
    enable_fivethirtyeight: bool = Field(
        default=False,
        alias="ENABLE_FIVETHIRTYEIGHT",
        description="Enable FiveThirtyEight SPI provider (CC BY 4.0)",
    )
    enable_wikipedia: bool = Field(
        default=False,
        alias="ENABLE_WIKIPEDIA",
        description="Enable Wikipedia/Wikidata provider (CC BY-SA 4.0)",
    )


# Global settings instance
settings = Settings()
