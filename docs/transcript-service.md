# Transcript scraper (`earnings_rag.transcripts`)

Downloads earnings call transcripts from Motley Fool and stores them as plain-text files. State is tracked in per-ticker JSON registries so runs are idempotent — safe to call on a cron.

## Quick start

```bash
# 1. Bootstrap a ticker — fetches earnings dates from yfinance, sets the
#    earliest_year floor, queues matching entries in the registry
earnings-transcripts init MSFT microsoft --from-year 2024

# 2. Download everything queued
earnings-transcripts
```

After bootstrap, step 2 is all that's needed for ongoing catch-up. Each run refreshes earnings dates from yfinance automatically before discovering new entries.

## CLI

```
earnings-transcripts [command] [options]
```

| Command | Description |
| ------- | ----------- |
| *(none)* | Alias for `sync` — the default catch-up command |
| `sync [ticker] [--retry]` | Refresh dates from yfinance, queue any new ones within the floor, then fetch all pending. Omit ticker to run all registered tickers. `--retry` re-attempts errored entries. |
| `init <ticker> <slug> --from-year YYYY` | Bootstrap a new ticker or update an existing one. Fetches earnings dates from yfinance, sets `company_slug` and `earliest_year`, and queues matching entries. `--from YYYY-MM-DD` optionally narrows the initial queue. |
| `add <ticker> <quarter> <year> [--url URL]` | Manually queue one fiscal quarter for an already-registered ticker. `--url` pins the exact Motley Fool URL, bypassing auto-construction. |
| `fetch` | Download pending entries across all tickers without refreshing or discovering dates. |
| `list` | Print registry status for all tickers. |

### `company_slug`

The Motley Fool URL slug for the company — visible in their transcript URLs:

```
fool.com/earnings/call-transcripts/2024/05/29/uipath-path-q1-2025-earnings-call-transcript/
                                               ^^^^^^
```

If you see "Could not find transcript at expected URL", the slug is wrong. Re-run `init` with the correct value.

## Files written

| Path | Contents |
| ---- | -------- |
| `data/transcripts/<TICKER>_Q<N>_FY<YYYY>.txt` | Scraped transcript text |
| `data/registry/<TICKER>_transcripts.json` | Per-ticker registry |
| `data/earnings_dates/earnings_dates_<TICKER>.json` | Earnings date cache (updated each run) |

## Registry schema

```json
{
  "ticker": "PATH",
  "company_slug": "uipath",
  "earliest_year": 2024,
  "entries": [
    {
      "quarter": 1,
      "year": 2025,
      "report_date": "2024/05/29",
      "status": "fetched"
    },
    {
      "quarter": 3,
      "year": 2025,
      "report_date": "2025/12/03",
      "url": "https://www.fool.com/earnings/call-transcripts/...",
      "status": "pending"
    }
  ]
}
```

**`earliest_year`** is the fetch floor: dates whose calendar year falls below it are never queued, even if yfinance returns them. Re-run `init` with a different `--from-year` to change it.

Entry statuses: `pending` → `fetched` or `error`. Errored entries gain an `"error"` field with the message. Re-attempt with `sync --retry`.

Legacy registries in plain list format are auto-migrated to this schema on first load.

## Module structure

| Module | Responsibility |
| ------ | -------------- |
| `../config.py` | Shared paths and env settings (package-wide) |
| `dates.py` | yfinance earnings date fetching and local cache management |
| `fiscal.py` | Fiscal calendar helpers (quarter/year mapping) |
| `fool.py` | Motley Fool URL construction and HTML scraping |
| `registry.py` | Registry I/O, schema, and legacy migration |
| `sync.py` | Date discovery (`queue_new_dates`) and fetch orchestration (`fetch_pending`) |
| `cli.py` | Argument parser and `cmd_*` functions |

## Programmatic use

```python
from earnings_rag.transcripts import load_ticker_registry, fetch_pending, save_ticker_registry
from earnings_rag.transcripts.dates import refresh_earnings_dates
from earnings_rag.transcripts.sync import queue_new_dates

registry = load_ticker_registry("PATH")
dates = refresh_earnings_dates("PATH")
queue_new_dates(registry, dates)
ok, failed = fetch_pending(registry)
save_ticker_registry("PATH", registry)
```