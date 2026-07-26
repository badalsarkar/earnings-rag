"""Earnings transcript downloader.

Registry schema (``data/registry/<TICKER>_transcripts.json``):

    {
      "ticker": "PATH",
      "company_slug": "uipath",
      "earliest_year": 2024,
      "fy_end_month": 12,
      "entries": [
        {"quarter": 1, "year": 2025, "report_date": "2024/05/29", "status": "fetched"},
        ...
      ]
    }

Legacy list-of-entries files are auto-migrated on first load.

Usage (CLI):
    earnings-transcripts                                  # sync all tickers
    earnings-transcripts sync [ticker] [--retry]
    earnings-transcripts init <ticker> <slug> --from-year YYYY
    earnings-transcripts add  <ticker> <quarter> <year>
    earnings-transcripts fetch
    earnings-transcripts list
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
