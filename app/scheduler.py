import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.logging_config import setup_logging
from app.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def job() -> None:
    try:
        run_pipeline()
    except Exception:
        logger.exception("Scheduled pipeline run failed")


def main() -> None:
    setup_logging()
    settings = get_settings()

    scheduler = BlockingScheduler(timezone=settings.scrape_timezone)
    scheduler.add_job(
        job,
        trigger=CronTrigger(hour=settings.scrape_cron_hour, minute=settings.scrape_cron_minute),
        id="daily_scrape",
        name="Daily K-pop news scrape",
        misfire_grace_time=3600,
    )

    logger.info(
        "Scheduler started: daily run at %02d:%02d %s",
        settings.scrape_cron_hour,
        settings.scrape_cron_minute,
        settings.scrape_timezone,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
