"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.database.session import init_db
from src.api.routes import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting Stryktips Bot application")
    init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down Stryktips Bot application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Automated Stryktips analysis with value betting",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
