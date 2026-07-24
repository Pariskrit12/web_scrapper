import logging
import re

from scrapling.fetchers import StealthyFetcher

from app.config import get_settings
from app.models import Article
from app.scrapers.base import BaseScraper, register
from app.scrapers.dateutils import parse_fuzzy_date

logger = logging.getLogger(__name__)

BASE_URL = "https://www.allkpop.com"

_WHITESPACE_RE = re.compile(r"\s+")


def _clean(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


@register
class AllkpopScraper(BaseScraper):
    """allkpop sits behind Cloudflare's managed challenge, so it needs a real
    headless browser (StealthyFetcher) rather than a plain HTTP request.
    There's no first-party listing endpoint reachable this way either, so this
    plugin uses the site's own Google Programmable Search widget
    (/search/articles/{slug}) as the article source."""

    name = "allkpop"

    def scrape_artist(self, artist_slug: str) -> list[Article]:
        settings = get_settings()
        url = f"{BASE_URL}/search/articles/{artist_slug}"
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            solve_cloudflare=True,
            timeout=settings.allkpop_cloudflare_timeout_ms,
        )

        articles: list[Article] = []
        for node in page.css(".gsc-webResult.gsc-result"):
            title_link = node.css(".gs-title a")
            if not title_link:
                continue
            title_link = title_link[0]

            link = title_link.attrib.get("href")
            title = _clean(title_link.get_all_text())
            if not link or not title:
                continue

            snippet = node.css(".gs-bidi-start-align.gs-snippet")
            snippet_text = snippet[0].get_all_text().strip() if snippet else None
            caption = None
            if snippet_text:
                # Snippet shape: "<date>\n...\n<description>"; keep just the description.
                parts = snippet_text.split("\n", 2)
                caption = _clean(parts[-1]).lstrip(". ").strip() or None

            articles.append(
                Article(
                    artist=artist_slug,
                    source=self.name,
                    title=title,
                    caption=caption,
                    link=link,
                    image=node.css("img::attr(src)").get(),
                    published_at=parse_fuzzy_date(snippet_text),
                )
            )

        logger.info("allkpop: parsed %d articles for '%s'", len(articles), artist_slug)
        return articles
