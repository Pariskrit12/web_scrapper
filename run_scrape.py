"""One-shot scrape run: scrape all sources, upsert into MongoDB, export Excel.

Used for manual runs and for the GitHub Actions cron workflow. For a
long-running deployment (VPS/EC2) that keeps scraping daily on its own,
use `app/scheduler.py` instead.
"""

from app.logging_config import setup_logging
from app.pipeline import run_pipeline


def main() -> None:
    setup_logging()
    run_pipeline()


if __name__ == "__main__":
    main()
