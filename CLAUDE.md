# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install / sync deps (uv-managed; installs the package in editable mode)
uv sync

# Start PostgreSQL + pgAdmin (pgvector/pg17); migrations/ auto-applies on first volume init
docker compose up -d

# Transcript scraper
uv run earnings-transcripts init MSFT microsoft --from-year 2024
uv run earnings-transcripts                 # sync all registered tickers (default)
uv run earnings-transcripts sync GOOGL --retry
uv run earnings-transcripts list

# Ingest
uv run earnings-load     # data/transcripts/*.txt → transcripts table
uv run earnings-embed    # transcripts table → transcript_chunks vectors

# API
./scripts/run-api.sh     # or: uv run uvicorn earnings_rag.api:app --reload

# Checks
uv run ruff check src/
uv run pytest
```

## Architecture

Single installable package under `src/`, built with hatchling. Console scripts are declared in `[project.scripts]`.

```
src/earnings_rag/
├── config.py        paths + env settings
├── transcripts/     Motley Fool scraper (cli, dates, fiscal, fool, registry, sync)
├── db/              connection.py (psycopg context manager) + transcripts.py (queries)
├── embeddings/      chunking.py (pure) + cohere_client.py (API calls)
├── ingest/          load.py, embed.py — batch jobs, each with a main() entry point
└── api/             app.py (FastAPI) + schemas.py (pydantic)

data/                transcripts/, registry/, earnings_dates/ — git-tracked state
migrations/          SQL, mounted into the Postgres container's init dir
docs/                journal.md, learning/, transcript-service.md
```

### Scraper data flow (per run)

1. **`dates.py`** — fetches earnings call dates from yfinance; merges with the JSON cache in `data/earnings_dates/`.
2. **`fiscal.py`** — maps a report date to `(quarter, fiscal_year)` using the ticker's `fy_end_month` (default 12). Earnings calls must fall within 90 days after the fiscal quarter end.
3. **`registry.py`** — reads/writes per-ticker JSON in `data/registry/`. Schema:
   ```json
   { "ticker", "company_slug", "earliest_year", "fy_end_month", "entries": [...] }
   ```
   Each entry: `{ "quarter", "year", "report_date" (YYYY/MM/DD), "status", "url", "error?" }`. Statuses: `pending → fetched | error`.
4. **`sync.py → queue_new_dates`** — appends `pending` entries for dates passing the `earliest_year` floor and not already present.
5. **`fool.py`** — `build_transcript_url` constructs Motley Fool URLs **without network I/O** (pure). `scrape_transcript` does the HTTP fetch and HTML parse.
6. **`sync.py → fetch_entry`** — tries all URL suffix variants in `fool.SUFFIXES` and writes text to `data/transcripts/<TICKER>_Q<N>_FY<YYYY>.txt`.

### Database layer

PostgreSQL + pgvector. `transcripts` (unique on `ticker, quarter, fiscal_year`) and `transcript_chunks` (unique on `transcript_id, chunk_index`). `db/connection.py` opens a fresh connection per call via a context manager.

## Key invariants

- **All env and path resolution lives in `config.py`.** No other module calls `os.getenv` or derives paths from its own `__file__`. Add new settings there.
- **`earliest_year` is the explicit fetch floor** — never infer it from data in the registry. It is always set by the caller via `--from-year` and stored verbatim.
- **`build_transcript_url` must remain pure** (no HTTP calls). Suffix fallback and URL probing live in `fetch_entry` in `sync.py`.
- **`embeddings/chunking.py` must not import cohere** — it takes a tokenizer as a parameter so the windowing logic stays testable. Cohere-specific wiring belongs in `cohere_client.py`.
- **Registry `report_date` format is `YYYY/MM/DD`** (slash-separated). The `normalize_report_date` helper enforces this.
- **Runs are idempotent** — `queue_new_dates` deduplicates by `report_date`; `fetch_entry` only processes `pending` entries. Safe for cron.
