import json
import logging

from scrapling.fetchers import Fetcher

from app.models import Article
from app.scrapers.base import BaseScraper, register
from app.scrapers.dateutils import parse_fuzzy_date

logger = logging.getLogger(__name__)

BASE_URL = "https://www.soompi.com"
API_URL = f"{BASE_URL}/wp-json/home/v1/get-tag-search-articles"


@register
class SoompiScraper(BaseScraper):
    name = "soompi"

    def scrape_artist(self, artist_slug: str) -> list[Article]:
        page = Fetcher.get(API_URL, params={"tag": artist_slug, "page": 1, "ltp": 0}, timeout=30)

        payload = json.loads(page.body)
        items = payload.get("data") or []

        articles: list[Article] = []
        for item in items:
            link = item.get("permalink")
            title = item.get("title")
            if not link or not title:
                continue

            articles.append(
                Article(
                    artist=artist_slug,
                    source=self.name,
                    title=title.strip(),
                    caption=None,
                    link=link,
                    image=item.get("featuredImageUrl"),
                    published_at=parse_fuzzy_date(item.get("createdOn")),
                )
            )

        logger.info("soompi: parsed %d articles for '%s'", len(articles), artist_slug)
        return articles
