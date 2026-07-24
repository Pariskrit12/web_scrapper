import logging

from scrapling.fetchers import Fetcher

from app.models import Article
from app.scrapers.base import BaseScraper, register
from app.scrapers.dateutils import parse_fuzzy_date

logger = logging.getLogger(__name__)

BASE_URL = "https://www.koreaboo.com"


@register
class KoreabooScraper(BaseScraper):
    name = "koreaboo"

    def scrape_artist(self, artist_slug: str) -> list[Article]:
        url = f"{BASE_URL}/artist/{artist_slug}/"
        page = Fetcher.get(url, timeout=30)

        articles: list[Article] = []
        for node in page.css("article.ap-chron-medium"):
            link = node.css("a::attr(href)").get()
            if not link:
                continue
            if link.startswith("/"):
                link = BASE_URL + link

            title = node.css(".ap-chron-medium-title::text").get()
            if not title:
                continue

            articles.append(
                Article(
                    artist=artist_slug,
                    source=self.name,
                    title=title.strip(),
                    caption=(node.css(".ap-chron-medium-caption::text").get() or "").strip() or None,
                    link=link,
                    image=node.css("img::attr(src)").get(),
                    published_at=parse_fuzzy_date(node.css("time::attr(datetime)").get()),
                )
            )

        logger.info("koreaboo: parsed %d articles for '%s'", len(articles), artist_slug)
        return articles
