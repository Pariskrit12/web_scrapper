"""Scraper plugin package.

Every module imported here registers itself (via the @register decorator in
base.py) into the shared registry. To add a new site: create a new module,
subclass BaseScraper, decorate with @register, and add one import line below.
"""

from app.scrapers import allkpop, koreaboo, soompi  # noqa: F401
from app.scrapers.base import get_registered_scrapers

__all__ = ["get_registered_scrapers"]
