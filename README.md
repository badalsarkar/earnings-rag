# earnings-rag

A pipeline for scraping earnings call transcripts from Motley Fool and storing them in a PostgreSQL (pgvector) database for retrieval-augmented generation (RAG) use cases.

## Layout

```
src/earnings_rag/
├── config.py        paths + env-derived settings (the only module reading os.environ)
├── transcripts/     scrape Motley Fool into data/, tracked in per-ticker JSON registries
├── db/              PostgreSQL persistence (connection.py, transcripts.py)
├── embeddings/      token chunking (chunking.py) + Cohere client (cohere_client.py)
├── ingest/          batch jobs: load.py (files → DB), embed.py (DB → vectors)
└── api/             FastAPI service (app.py, schemas.py)

data/                transcripts/, registry/, earnings_dates/   (git-tracked state)
migrations/          SQL, auto-applied by docker compose on first DB init
docs/                journal.md, learning/, transcript-service.md
scripts/             run-api.sh
tests/
```

## Setup

**1. Configure**

```bash
cp .env.example .env   # then fill in credentials + CO_API_KEY
```

**2. Start the database**

```bash
docker compose up -d
```

PostgreSQL (pgvector/pg17) on port 5432, pgAdmin on 5050. `migrations/` is mounted into the container's init directory, so the schema is applied automatically the first time the data volume is created. To apply migrations to an existing volume:

```bash
psql -h localhost -U postgres -d earnings -f migrations/001_create_transcripts.sql
psql -h localhost -U postgres -d earnings -f migrations/002_create_transcript_chunks.sql
```

**3. Install**

```bash
uv sync
```

This installs the project in editable mode and puts the CLIs on `PATH` (prefix with `uv run`, or activate `.venv`).

## Fetching transcripts

**Bootstrap a ticker** — fetches earnings dates from yfinance, queues entries back to `--from-year`:

```bash
uv run earnings-transcripts init GOOGL alphabet --from-year 2023
uv run earnings-transcripts init PATH uipath --from-year 2024 --fy-end-month 1
```

The `company_slug` is the company name as it appears in Motley Fool transcript URLs:
```
fool.com/earnings/call-transcripts/2024/05/29/uipath-path-q1-2025-earnings-call-transcript/
                                               ^^^^^^
```

**Sync and fetch** (discovers new dates, downloads pending transcripts):

```bash
uv run earnings-transcripts                 # all registered tickers
uv run earnings-transcripts sync GOOGL
uv run earnings-transcripts sync --retry    # also re-attempt errored entries
```

**Other commands:**

```bash
uv run earnings-transcripts list            # show registry status
uv run earnings-transcripts fetch           # download pending only, no discovery
uv run earnings-transcripts add PATH 2 2026 --url https://www.fool.com/...
```

Transcripts are saved to `data/transcripts/<TICKER>_Q<N>_FY<YYYY>.txt`. Runs are idempotent and safe for cron.

## Loading and embedding

```bash
uv run earnings-load     # data/transcripts/*.txt → transcripts table
uv run earnings-embed    # transcripts table → chunked vectors in transcript_chunks
```

`earnings-load` looks up each file's `report_date` from the registry and upserts. `earnings-embed` chunks with the embedding model's own tokenizer (400 tokens, 50 overlap) and writes to `transcript_chunks`.

## Running the API

```bash
./scripts/run-api.sh
# or: uv run uvicorn earnings_rag.api:app --reload
```

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `PUT /transcripts` | Upsert a transcript |
| `GET /transcripts/{ticker}` | List all transcripts for a ticker |
| `GET /transcripts/{ticker}/q{quarter}/{fiscal_year}` | Get a specific transcript |

## Development

```bash
uv run ruff check src/
uv run pytest
```

## Environment variables

Loaded from `.env` at the repo root automatically. See `.env.example`.

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | |
| `POSTGRES_PORT` | `5432` | |
| `POSTGRES_DB` | `earnings` | |
| `POSTGRES_USER` | `postgres` | |
| `POSTGRES_PASSWORD` | `postgres` | |
| `CO_API_KEY` | — | Cohere API key, read by the Cohere SDK |
| `EARNINGS_DATA_DIR` | `./data` | Override the data directory root |
| `LOG_LEVEL` | `INFO` | |
