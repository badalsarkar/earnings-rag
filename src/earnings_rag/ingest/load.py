"""Load scraped transcript .txt files into the database."""
import logging
import re
from datetime import date

from ..config import TRANSCRIPTS_DIR, configure_logging, load_env
from ..db import upsert_transcript
from ..transcripts.registry import load_ticker_registry

logger = logging.getLogger(__name__)

FILENAME_RE = re.compile(r"^(?P<ticker>[A-Z]+)_Q(?P<quarter>\d)_FY(?P<year>\d{4})\.txt$")


def _report_date(ticker: str, quarter: int, fiscal_year: int) -> date | None:
    """Look up an entry's report_date in the ticker's registry."""
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
    logger.info("Found %d transcript files in %s", len(files), TRANSCRIPTS_DIR)

    loaded = skipped = 0
    for path in files:
        m = FILENAME_RE.match(path.name)
        if not m:
            logger.warning("Skipping %s: unrecognised filename", path.name)
            skipped += 1
            continue

        ticker = m.group("ticker")
        quarter = int(m.group("quarter"))
        fiscal_year = int(m.group("year"))

        report_date = _report_date(ticker, quarter, fiscal_year)
        if report_date is None:
            logger.warning("Skipping %s: no report_date in registry", path.name)
            skipped += 1
            continue

        content = path.read_text(encoding="utf-8")
        upsert_transcript(ticker, quarter, fiscal_year, report_date, content)
        logger.info("Loaded %s (%d chars)", path.name, len(content))
        loaded += 1

    logger.info("Done: %d loaded, %d skipped", loaded, skipped)


def main() -> None:
    load_env()
    configure_logging()
    load_all()


if __name__ == "__main__":
    main()
