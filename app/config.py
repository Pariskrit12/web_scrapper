from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "kpop_news"
    mongo_collection: str = "articles"

    scrape_cron_hour: int = 6
    scrape_cron_minute: int = 0
    scrape_timezone: str = "UTC"

    excel_export_path: str = "kpop_news.xlsx"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    allkpop_cloudflare_timeout_ms: int = 45000


@lru_cache
def get_settings() -> Settings:
    return Settings()
