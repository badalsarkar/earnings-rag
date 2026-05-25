import json
from pathlib import Path

from fool_service import get_earnings_transcript
from transcript_service.paths import TRANSCRIPTS_DIR
from transcript_service.registry import (
    all_registered_tickers,
    load_ticker_registry,
    save_ticker_registry,
)


def fetch_pending() -> None:
    for ticker in all_registered_tickers():
        registry = load_ticker_registry(ticker)
        if registry is None:
            continue

        changed = False
        for entry in registry["entries"]:
            if entry["status"] != "pending":
                continue

            quarter, year = entry["quarter"], entry["year"]
            print(f"Fetching {ticker} Q{quarter} FY{year} ...")
            try:
                transcript = get_earnings_transcript(ticker, quarter, year, url=entry.get("url"))
                TRANSCRIPTS_DIR.mkdir(exist_ok=True)
                path = TRANSCRIPTS_DIR / f"{ticker}_Q{quarter}_FY{year}.txt"
                path.write_text(transcript, encoding="utf-8")
                entry["status"] = "fetched"
                print(f"  Saved {len(transcript):,} chars -> {path}")
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
                print(f"  Error: {e}")
            changed = True

        if changed:
            save_ticker_registry(ticker, registry)


if __name__ == "__main__":
    fetch_pending()