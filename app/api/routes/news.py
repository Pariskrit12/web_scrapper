from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.artists import ARTISTS
from app.config import get_settings
from app.db import get_collection
from app.scrapers import get_registered_scrapers

router = APIRouter()


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/sources")
def list_sources() -> dict:
    return {"sources": list(get_registered_scrapers().keys())}


@router.get("/artists")
def list_artists() -> dict:
    return {"artists": ARTISTS}


@router.get("/export")
def download_export() -> FileResponse:
    """Download the latest full Excel export (regenerated on every scrape run)."""
    settings = get_settings()
    path = Path(settings.excel_export_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="No export yet — pipeline hasn't run.")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="kpop_news.xlsx",
    )


@router.get("/articles")
def list_articles(
    artist: Optional[str] = Query(None, description="Filter by artist slug, e.g. 'bts'"),
    source: Optional[str] = Query(None, description="Filter by source, e.g. 'koreaboo'"),
    published_after: Optional[datetime] = Query(None),
    published_before: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, description="Case-insensitive title substring search"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    collection = get_collection()

    query: dict = {}
    if artist:
        query["artist"] = artist
    if source:
        query["source"] = source
    if search:
        query["title"] = {"$regex": search, "$options": "i"}
    if published_after or published_before:
        date_filter = {}
        if published_after:
            date_filter["$gte"] = published_after
        if published_before:
            date_filter["$lte"] = published_before
        query["published_at"] = date_filter

    total = collection.count_documents(query)
    cursor = (
        collection.find(query)
        .sort("published_at", -1)
        .skip(offset)
        .limit(limit)
    )
    items = [_serialize(doc) for doc in cursor]

    return {
        "total": total,
        "count": len(items),
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get("/articles/{article_id}")
def get_article(article_id: str) -> dict:
    from bson import ObjectId
    from bson.errors import InvalidId

    collection = get_collection()
    try:
        doc = collection.find_one({"_id": ObjectId(article_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Article not found")
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return _serialize(doc)
