# earnings-rag

A pipeline for scraping earnings call transcripts from Motley Fool and storing them in a PostgreSQL database for retrieval-augmented generation (RAG) use cases.

## Components

| Component | Description |
|-----------|-------------|
| `transcript_service/` | Scraper module — fetches transcripts from Motley Fool, tracks state in per-ticker JSON registries |
| `api.py` + `db_service.py` | FastAPI HTTP API over PostgreSQL (pgvector) |
| `load_transcripts.py` | Loads scraped `.txt` files into the database |

## Setup

**1. Start the database**

```bash
docker compose up -d
```

This starts PostgreSQL (pgvector/pg17) on port 5432 and pgAdmin on port 5050. Copy `.env.example` to `.env` and fill in credentials, or the defaults (`postgres`/`postgres`, db `earnings`) will be used.

**2. Apply the schema**

```bash
psql -h localhost -U postgres -d earnings -f db/migrations/001_create_transcripts.sql
```

**3. Install Python dependencies**

```bash
pip install fastapi uvicorn psycopg requests beautifulsoup4 yfinance python-dotenv cohere
```

## Fetching Transcripts

**Bootstrap a ticker** — fetches earnings dates from yfinance, queues entries back to `--from-year`:

```bash
python -m transcript_service init GOOGL alphabet --from-year 2023
python -m transcript_service init PATH uipath --from-year 2024
```

The `company_slug` is the company name as it appears in Motley Fool transcript URLs:
```
fool.com/earnings/call-transcripts/2024/05/29/uipath-path-q1-2025-earnings-call-transcript/
                                               ^^^^^^
```

**Sync and fetch** (discovers new dates, downloads pending transcripts):

```bash
python -m transcript_service          # all registered tickers
python -m transcript_service sync GOOGL
python -m transcript_service sync --retry   # also re-attempt errored entries
```

**Other commands:**

```bash
python -m transcript_service list           # show registry status
python -m transcript_service fetch          # download pending only, no discovery
python -m transcript_service add PATH 2 2026 --url https://www.fool.com/...
```

Transcripts are saved to `output/transcripts/<TICKER>_Q<N>_FY<YYYY>.txt`.

## Loading into the Database

```bash
python load_transcripts.py
```

Reads all `.txt` files from `output/transcripts/`, looks up `report_date` from the registry, and upserts into the `transcripts` table.

## Running the API

```bash
uvicorn api:app --reload
```

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `PUT /transcripts` | Upsert a transcript |
| `GET /transcripts/{ticker}` | List all transcripts for a ticker |
| `GET /transcripts/{ticker}/q{quarter}/{fiscal_year}` | Get a specific transcript |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | |
| `POSTGRES_PORT` | `5432` | |
| `POSTGRES_DB` | `earnings` | |
| `POSTGRES_USER` | `postgres` | |
| `POSTGRES_PASSWORD` | `postgres` | |
