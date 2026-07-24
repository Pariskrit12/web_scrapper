# K-pop News Aggregator

Scrapes K-pop news from multiple sites (koreaboo, soompi, allkpop), dedupes by
URL, stores in MongoDB, exports to Excel, and serves a read-only REST API.
Runs daily via APScheduler (long-lived deployment) or via GitHub Actions cron
(scrape-only, no persistent API).

## Architecture

```
app/
  config.py          settings from env / .env
  logging_config.py  console + file logging
  db.py              MongoDB client, indexes
  models.py          Article schema
  artists.py         list of artist slugs to track
  scrapers/
    base.py          BaseScraper interface + plugin registry
    koreaboo.py       plain HTTP (Fetcher)
    soompi.py         first-party wp-json API
    allkpop.py        headless browser + Cloudflare solve (Google CSE widget)
  pipeline.py         scrape -> dedupe -> mongo upsert -> excel export
  scheduler.py        APScheduler daily job (long-running process)
  api/
    main.py           FastAPI app
    routes/news.py    GET /articles, /artists, /sources, /health
run_scrape.py         one-shot scrape (manual / GitHub Actions)
run_server.py         uvicorn entrypoint
```

### Adding a new scraper

1. Create `app/scrapers/<site>.py`, subclass `BaseScraper`, implement
   `scrape_artist(artist_slug) -> list[Article]`, decorate with `@register`.
2. Add `from app.scrapers import <site>` to `app/scrapers/__init__.py`.

No other file changes needed — `pipeline.py` and the API pick up every
registered scraper automatically.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium   # needed for the allkpop scraper

cp .env.example .env   # set MONGO_URI to your Atlas connection string

python run_scrape.py          # one-shot scrape + excel export
python run_server.py          # API on :8000
python -m app.scheduler       # daily scheduler (long-running)
```

API docs at `http://localhost:8000/docs` once the server is running.

## Deploy on a VPS (Docker Compose)

```bash
cp .env.example .env   # fill in MONGO_URI (Atlas) and other settings
docker compose up -d --build
```

This runs two containers from the same image:
- `api` — FastAPI on `API_PORT` (default 8000)
- `scheduler` — daily scrape job, exports Excel to `./exports/kpop_news.xlsx`

Logs land in `./logs` on the host (bind-mounted). Update by pulling new code
and running `docker compose up -d --build` again.

## GitHub Actions (scrape-only cron)

`.github/workflows/scrape.yml` runs the scrape daily at 06:00 UTC and uploads
the Excel export as a workflow artifact. Set repo secret `MONGO_URI` (Atlas
connection string) before enabling it. This path does not host the API —
pair it with the VPS deployment above if you need the API live, or run
`run_server.py` separately wherever you want it reachable.

## Notes on sources

- **koreaboo** and **soompi** are scraped with plain HTTP requests.
- **allkpop** sits behind a Cloudflare managed challenge, so it's scraped
  with a headless browser (`solve_cloudflare=True`) hitting the site's own
  Google Programmable Search widget at `/search/articles/{slug}`, since
  there's no plain listing page reachable without solving the challenge.
  Dates on allkpop are best-effort parsed from relative/absolute strings
  ("3 days ago", "Jun 10, 2026") since that's all the search widget exposes.
