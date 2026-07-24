import logging

import pandas as pd
from pymongo import ReplaceOne

from app.artists import ARTISTS
from app.config import get_settings
from app.db import get_collection
from app.models import Article
from app.scrapers import get_registered_scrapers

logger = logging.getLogger(__name__)


def run_all_scrapers() -> list[Article]:
    """Run every registered scraper plugin against every configured artist.
    A failure in one scraper/artist pair is logged and skipped so one bad
    site or one bad artist page never aborts the whole run."""
    scrapers = get_registered_scrapers()
    collected: list[Article] = []

    for scraper_name, scraper in scrapers.items():
        for artist in ARTISTS:
            try:
                articles = scraper.scrape_artist(artist)
                collected.extend(articles)
            except Exception:
                logger.exception("Scraper '%s' failed for artist '%s'", scraper_name, artist)

    return collected


def dedupe_articles(articles: list[Article]) -> list[Article]:
    """Dedupe within a single run by link, keeping the last-seen copy."""
    by_link: dict[str, Article] = {}
    for article in articles:
        by_link[article.link] = article
    return list(by_link.values())


def upsert_articles(articles: list[Article]) -> int:
    """Upsert into MongoDB keyed on the unique `link` index. Existing
    documents are fully replaced so re-scrapes pick up title/caption edits;
    `scraped_at` naturally advances, `published_at` stays whatever the source
    reports on that run."""
    if not articles:
        return 0

    collection = get_collection()
    operations = [
        ReplaceOne({"link": article.link}, article.to_mongo(), upsert=True)
        for article in articles
    ]
    result = collection.bulk_write(operations, ordered=False)
    upserted = result.upserted_count
    modified = result.modified_count
    logger.info("Mongo upsert: %d new, %d updated", upserted, modified)
    return upserted + modified


def export_to_excel(path: str | None = None) -> int:
    """Export the full current collection state to an Excel workbook."""
    settings = get_settings()
    path = path or settings.excel_export_path

    collection = get_collection()
    documents = list(collection.find({}, {"_id": 0}).sort("published_at", -1))

    df = pd.DataFrame(documents)
    df.to_excel(path, index=False)
    logger.info("Exported %d articles to %s", len(df), path)
    return len(df)


def run_pipeline() -> dict:
    logger.info("Pipeline run starting")
    scraped = run_all_scrapers()
    logger.info("Scraped %d raw articles across all sources", len(scraped))

    deduped = dedupe_articles(scraped)
    logger.info("Deduped to %d unique articles for this run", len(deduped))

    written = upsert_articles(deduped)
    exported = export_to_excel()

    summary = {
        "scraped": len(scraped),
        "deduped": len(deduped),
        "written_to_mongo": written,
        "exported_to_excel": exported,
    }
    logger.info("Pipeline run finished: %s", summary)
    return summary
