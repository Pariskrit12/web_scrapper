import logging
from abc import ABC, abstractmethod

from app.models import Article

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, "BaseScraper"] = {}


def register(cls: type["BaseScraper"]) -> type["BaseScraper"]:
    """Class decorator: instantiates and registers a scraper plugin by its `name`."""
    instance = cls()
    if instance.name in _REGISTRY:
        raise ValueError(f"Duplicate scraper name: {instance.name}")
    _REGISTRY[instance.name] = instance
    return cls


def get_registered_scrapers() -> dict[str, "BaseScraper"]:
    return dict(_REGISTRY)


class BaseScraper(ABC):
    """Base interface every site plugin must implement.

    Add a new site: subclass BaseScraper, set `name`, implement `scrape_artist`,
    decorate the class with @register, and import the module in
    app/scrapers/__init__.py. No other file needs to change.
    """

    name: str

    @abstractmethod
    def scrape_artist(self, artist_slug: str) -> list[Article]:
        """Fetch and parse articles for one artist slug. Must not raise on
        expected per-item parse gaps; only raise for fetch-level failures."""
        raise NotImplementedError
