# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start PostgreSQL + pgAdmin (pgvector/pg17)
docker compose up -d

# Transcript service — bootstrap a ticker and fetch transcripts
python -m transcript_service init MSFT microsoft --from-year 2024
python -m transcript_service          # sync all registered tickers (default)
python -m transcript_service sync GOOGL --retry
python -m transcript_service list

# Load scraped .txt files into the database
python load_transcripts.py            # requires .env / env vars

# Run the FastAPI service
uvicorn api:app --reload
```

Dependencies are not managed by a `pyproject.toml`; install manually (`psycopg`, `fastapi`, `uvicorn`, `requests`, `beautifulsoup4`, `yfinance`, `python-dotenv`, `cohere`).

## Architecture

```
transcript_service/     ← scraper module (primary active code)
api.py + db_service.py  ← FastAPI HTTP API over Postgres
load_transcripts.py     ← one-off loader: .txt files → DB
cohere_service.py       ← early Cohere stub (unused)
fool_service.py         ← legacy scraper (superseded by transcript_service/fool.py)
main.py                 ← legacy fetch runner (superseded by transcript_service CLI)
```

### transcript_service/ module

The module is the active scraping pipeline. Data flow per run:

1. **`dates.py`** — fetches earnings call dates from yfinance; merges with a local JSON cache in `transcript_service/earnings_dates/`.
2. **`fiscal.py`** — maps a report date to `(quarter, fiscal_year)` using the ticker's `fy_end_month` (default 12). Earnings calls must fall within 90 days after the fiscal quarter end.
3. **`registry.py`** — reads/writes per-ticker JSON files in `transcript_service/transcripts_registry/`. The registry object schema:
   ```json
   { "ticker", "company_slug", "earliest_year", "fy_end_month", "entries": [...] }
   ```
   Each entry: `{ "quarter", "year", "report_date" (YYYY/MM/DD), "status", "url", "error?" }`. Statuses: `pending → fetched | error`.
4. **`sync.py → queue_new_dates`** — appends `pending` entries for dates that pass the `earliest_year` floor and are not already present.
5. **`fool.py`** — `build_transcript_url` constructs Motley Fool URLs **without network I/O** (pure function). `scrape_transcript` performs the actual HTTP fetch and HTML parse.
6. **`sync.py → fetch_entry`** — tries all URL suffix variants (`earnings-call-transcript`, `earnings-transcript`) and writes the scraped text to `output/transcripts/<TICKER>_Q<N>_FY<YYYY>.txt`.

### Database layer

PostgreSQL (pgvector) stores transcripts in a single `transcripts` table (unique on `ticker, quarter, fiscal_year`). `db_service.py` opens a fresh connection per call via a context manager. Env vars: `POSTGRES_HOST/PORT/DB/USER/PASSWORD` (defaults match `docker-compose.yml`). `db/migrations/001_create_transcripts.sql` must be applied manually before use.

## Key invariants

- **`earliest_year` is the explicit fetch floor** — never infer it from data in the registry. It is always set by the caller via `--from-year` and stored verbatim.
- **`build_transcript_url` must remain pure** (no HTTP calls). Suffix fallback and URL probing live in `fetch_entry` in `sync.py`.
- **Registry `report_date` format is `YYYY/MM/DD`** (slash-separated). The `normalize_report_date` helper enforces this.
- **Runs are idempotent** — `queue_new_dates` deduplicates by `report_date`; `fetch_entry` only processes `pending` entries. Safe for cron.
