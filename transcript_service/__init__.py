"""Earnings transcript downloader.

Registry schema (``transcripts_registry/<TICKER>_transcripts.json``):

    {
      "ticker": "PATH",
      "company_slug": "uipath",
      "earliest_year": 2024,
      "entries": [
        {"quarter": 1, "year": 2025, "report_date": "2024/05/29", "status": "fetched"},
        ...
      ]
    }

Legacy list-of-entries files are auto-migrated on first load.

Usage (CLI):
    python -m transcript_service                                  # sync all tickers
    python -m transcript_service sync [ticker] [--retry]
    python -m transcript_service init <ticker> <slug> --from-year YYYY
    python -m transcript_service add  <ticker> <quarter> <year>
    python -m transcript_service fetch
    python -m transcript_service list
"""
from .registry import (
    all_registered_tickers,
    load_ticker_registry,
    new_registry,
    save_ticker_registry,
)
from .sync import fetch_entry, fetch_pending, queue_new_dates

__all__ = [
    "all_registered_tickers",
    "load_ticker_registry",
    "new_registry",
    "save_ticker_registry",
    "fetch_entry",
    "fetch_pending",
    "queue_new_dates",
]