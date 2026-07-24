from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class Article(BaseModel):
    artist: str
    source: str
    title: str
    caption: Optional[str] = None
    link: str
    image: Optional[str] = None
    published_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mongo(self) -> dict:
        return self.model_dump()


class ArticleOut(Article):
    id: str = Field(alias="_id")

    model_config = {"populate_by_name": True}
