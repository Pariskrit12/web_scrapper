import logging
from functools import lru_cache

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongo_uri)


def get_collection() -> Collection:
    settings = get_settings()
    client = get_client()
    collection = client[settings.mongo_db][settings.mongo_collection]
    collection.create_index([("link", ASCENDING)], unique=True)
    collection.create_index([("artist", ASCENDING)])
    collection.create_index([("source", ASCENDING)])
    collection.create_index([("published_at", ASCENDING)])
    return collection
