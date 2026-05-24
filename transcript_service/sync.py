"""Earnings date discovery (queueing) and transcript fetch orchestration."""
import sys
from datetime import date

from .fiscal import find_fiscal_quarter, fiscal_year_end_month, get_earnings_call_date
from .fool import _SUFFIXES, build_transcript_url, scrape_transcript
from .paths import TRANSCRIPTS_DIR
from .registry import normalize_report_date, transcript_path


def queue_new_dates(
    registry: dict,
    dates: list[str],
    from_date: date | None = None,
) -> int:
    """Append pending entries for earnings dates above the registry's floor.

    Skips dates that are in the future, below ``earliest_year``, below
    ``from_date`` (if given), or already present in entries (dedupe by
    ``report_date``). Returns the number of new entries added.
    """
    ticker = registry["ticker"]
    company_slug = registry.get("company_slug", "")
    earliest_year = registry["earliest_year"]
    entries = registry["entries"]
    today = date.today()
    existing_dates = {normalize_report_date(e.get("report_date")) for e in entries}
    fy_end_month: int | None = None
    added = 0

    for d_str in dates:
        d = date.fromisoformat(d_str)
        if d.year < earliest_year or d > today:
            continue
        if from_date and d < from_date:
            continue
        report_date = d.strftime("%Y/%m/%d")
        if report_date in existing_dates:
            continue

        if fy_end_month is None:
            print(f"  Querying fiscal calendar for {ticker} ...")
            fy_end_month = fiscal_year_end_month(ticker)

        try:
            quarter, year = find_fiscal_quarter(d, fy_end_month)
        except ValueError as exc:
            print(f"  Warning: {exc}", file=sys.stderr)
            continue

        url = None
        if company_slug:
            try:
                url = build_transcript_url(company_slug, ticker, quarter, year, report_date)
            except ValueError:
                pass

        entries.append({
            "quarter": quarter,
            "year": year,
            "report_date": report_date,
            "status": "pending",
            "url": url,
        })
        existing_dates.add(report_date)
        added += 1
        print(f"  Queued {ticker} Q{quarter} FY{year} ({d_str})")

    return added


def resolve_pending_urls(registry: dict) -> int:
    """Try to resolve the URL for every pending entry that still has url=None.

    Mutates entries in place. Returns the count of newly resolved URLs.
    """
    ticker = registry["ticker"]
    company_slug = registry.get("company_slug", "")
    if not company_slug:
        return 0
    resolved = 0
    for entry in registry["entries"]:
        if entry.get("status") != "pending" or entry.get("url"):
            continue
        report_date = entry.get("report_date")
        if not report_date:
            continue
        try:
            url = build_transcript_url(
                company_slug, ticker, entry["quarter"], entry["year"],
                report_date.replace("-", "/"),
            )
            entry["url"] = url
            resolved += 1
            print(f"  Resolved URL for {ticker} Q{entry['quarter']} FY{entry['year']}")
        except ValueError:
            pass
    return resolved


def fetch_entry(entry: dict, ticker: str, company_slug: str) -> bool:
    """Download a single entry. Mutates ``entry`` in place; returns True on success."""
    quarter = entry["quarter"]
    year = entry["year"]
    print(f"Fetching {ticker} Q{quarter} FY{year} ...")
    try:
        report_date = entry.get("report_date") or get_earnings_call_date(ticker, quarter, year)
        report_date_slash = report_date.replace("-", "/")
        stored_url = entry.get("url")
        urls_to_try = (
            [stored_url]
            if stored_url
            else [build_transcript_url(company_slug, ticker, quarter, year, report_date_slash, s)
                  for s in _SUFFIXES]
        )
        transcript = url = None
        last_exc: Exception | None = None
        for candidate in urls_to_try:
            try:
                transcript = scrape_transcript(candidate)
                url = candidate
                break
            except Exception as exc:
                last_exc = exc
        if transcript is None:
            raise last_exc  # type: ignore[misc]
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        path = transcript_path(ticker, entry)
        path.write_text(transcript, encoding="utf-8")
        entry["status"] = "fetched"
        entry["url"] = url
        entry["report_date"] = report_date_slash
        entry.pop("error", None)
        print(f"  Saved {len(transcript):,} chars -> {path}")
        return True
    except Exception as exc:
        entry["status"] = "error"
        entry["error"] = str(exc)
        print(f"  Error: {exc}", file=sys.stderr)
        return False


def fetch_pending(registry: dict) -> tuple[int, int]:
    """Fetch every pending entry in ``registry``. Returns ``(ok, failed)``."""
    ticker = registry["ticker"]
    company_slug = registry["company_slug"]
    if not company_slug:
        print(f"  {ticker}: missing company_slug in registry; cannot fetch.", file=sys.stderr)
        return 0, 0
    ok = failed = 0
    for entry in registry["entries"]:
        if entry.get("status") != "pending":
            continue
        if fetch_entry(entry, ticker, company_slug):
            ok += 1
        else:
            failed += 1
    return ok, failed