"""Earnings dates cache backed by yfinance."""
import json
from pathlib import Path

import yfinance as yf

from ..config import EARNINGS_DATES_DIR


def _dates_file(ticker: str) -> Path:
    return EARNINGS_DATES_DIR / f"earnings_dates_{ticker}.json"


def load_earnings_dates(ticker: str) -> list[str]:
    """Return stored earnings dates for ticker, or [] if none exist."""
    path = _dates_file(ticker)
    if not path.exists():
        return []
    return json.loads(path.read_text()).get("dates", [])


def _fetch_from_yfinance(ticker: str, limit: int = 100) -> list[str]:
    t = yf.Ticker(ticker)
    try:
        df = t.get_earnings_dates(limit=limit)
    except TypeError:
        df = t.earnings_dates
    if df is None or df.empty:
        raise ValueError(f"No earnings dates found for {ticker} via yfinance")
    return [
        (dt.date() if hasattr(dt, "date") else dt).strftime("%Y-%m-%d")
        for dt in sorted(df.index)
    ]


def refresh_earnings_dates(ticker: str) -> list[str]:
    """Fetch from yfinance, merge with stored dates, persist, and return all (sorted).

    Safe to call repeatedly — only new dates are added.
    """
    existing = load_earnings_dates(ticker)
    print(f"  Refreshing earnings dates for {ticker} from yfinance ...")
    fetched = _fetch_from_yfinance(ticker)
    merged = sorted(set(existing) | set(fetched))
    added = len(merged) - len(existing)
    EARNINGS_DATES_DIR.mkdir(exist_ok=True)
    _dates_file(ticker).write_text(json.dumps({"ticker": ticker, "dates": merged}, indent=2))
    if added:
        print(f"  +{added} new date(s), {len(merged)} total")
    else:
        print(f"  No new dates ({len(merged)} stored)")
    return merged