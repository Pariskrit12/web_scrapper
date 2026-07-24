from fastapi import FastAPI

from app.api.routes.news import router as news_router
from app.logging_config import setup_logging
from app.scrapers import get_registered_scrapers  # noqa: F401  (ensures plugins register)

setup_logging()

app = FastAPI(
    title="K-pop News API",
    description="Read-only API over aggregated, deduplicated K-pop news scraped from multiple sources.",
    version="1.0.0",
)

app.include_router(news_router)
