"""Per-ticker registry I/O, schema definition, and legacy migration."""
import json
from datetime import date
from pathlib import Path

from .paths import TRANSCRIPTS_DIR, TRANSCRIPTS_REGISTRY_DIR


def registry_path(ticker: str) -> Path:
    return TRANSCRIPTS_REGISTRY_DIR / f"{ticker}_transcripts.json"


def transcript_path(ticker: str, entry: dict) -> Path:
    return TRANSCRIPTS_DIR / f"{ticker}_Q{entry['quarter']}_FY{entry['year']}.txt"


def normalize_report_date(value: str | None) -> str | None:
    """Return the report date in 'YYYY/MM/DD' form, or None."""
    return value.replace("-", "/") if value else None


def new_registry(
    ticker: str, company_slug: str, earliest_year: int, fy_end_month: int = 12
) -> dict:
    return {
        "ticker": ticker,
        "company_slug": company_slug,
        "earliest_year": earliest_year,
        "fy_end_month": fy_end_month,
        "entries": [],
    }


def _migrate_legacy(ticker: str, entries: list[dict]) -> dict:
    """Convert a legacy list-of-entries file into the current object schema."""
    company_slug = next(
        (e.get("company_slug", "") for e in entries if e.get("company_slug")), ""
    )
    report_years = []
    for e in entries:
        rd = e.get("report_date")
        if rd:
            try:
                report_years.append(int(rd.replace("-", "/").split("/")[0]))
            except (ValueError, IndexError):
                pass
    earliest_year = min(report_years) if report_years else date.today().year
    cleaned = [
        {k: v for k, v in e.items() if k not in ("ticker", "company_slug")}
        for e in entries
    ]
    return {
        "ticker": ticker,
        "company_slug": company_slug,
        "earliest_year": earliest_year,
        "entries": cleaned,
    }


def load_ticker_registry(ticker: str) -> dict | None:
    """Load a ticker's registry. Returns None if the file doesn't exist.

    Legacy list-format files are auto-migrated to the current object schema
    in memory; the on-disk file is updated on the next save.
    """
    path = registry_path(ticker)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    if isinstance(data, list):
        data = _migrate_legacy(ticker, data)
    data.setdefault("entries", [])
    return data


def save_ticker_registry(ticker: str, registry: dict) -> None:
    TRANSCRIPTS_REGISTRY_DIR.mkdir(exist_ok=True)
    registry_path(ticker).write_text(json.dumps(registry, indent=2))


def all_registered_tickers() -> list[str]:
    if not TRANSCRIPTS_REGISTRY_DIR.exists():
        return []
    return sorted(
        f.stem.replace("_transcripts", "")
        for f in TRANSCRIPTS_REGISTRY_DIR.glob("*_transcripts.json")
    )