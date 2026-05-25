"""Load transcript .txt files from output/transcripts/ into the database."""
import re
from datetime import date
from pathlib import Path

import db_service
from transcript_service.registry import load_ticker_registry

TRANSCRIPTS_DIR = Path("output/transcripts")
FILENAME_RE = re.compile(r"^(?P<ticker>[A-Z]+)_Q(?P<quarter>\d)_FY(?P<year>\d{4})\.txt$")


def _report_date(ticker: str, quarter: int, fiscal_year: int) -> date | None:
    registry = load_ticker_registry(ticker)
    if registry is None:
        return None
    for entry in registry["entries"]:
        if entry["quarter"] == quarter and entry["year"] == fiscal_year:
            rd = entry.get("report_date")
            if rd:
                return date.fromisoformat(rd.replace("/", "-"))
    return None


def load_all() -> None:
    files = sorted(TRANSCRIPTS_DIR.glob("*.txt"))
    print(f"Found {len(files)} transcript files")

    for path in files:
        m = FILENAME_RE.match(path.name)
        if not m:
            print(f"  Skipping {path.name} (unrecognised filename)")
            continue

        ticker = m.group("ticker")
        quarter = int(m.group("quarter"))
        fiscal_year = int(m.group("year"))

        report_date = _report_date(ticker, quarter, fiscal_year)
        if report_date is None:
            print(f"  Skipping {path.name} (no report_date in registry)")
            continue

        content = path.read_text(encoding="utf-8")
        db_service.upsert_transcript(ticker, quarter, fiscal_year, report_date, content)
        print(f"  Loaded {path.name} ({len(content):,} chars)")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    load_all()
