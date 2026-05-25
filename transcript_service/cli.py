"""CLI commands and argument parser for transcript_service."""
import argparse
import sys
from datetime import date

from .dates import refresh_earnings_dates
from .fiscal import find_fiscal_quarter
from .paths import TRANSCRIPTS_DIR
from .registry import (
    all_registered_tickers,
    load_ticker_registry,
    new_registry,
    registry_path,
    save_ticker_registry,
    transcript_path,
)
from .sync import fetch_pending, queue_new_dates, resolve_pending_urls


def _recalculate_quarters(registry: dict, fy_end_month: int) -> None:
    """Recompute quarter/year for all entries from their stored report_date.

    For non-fetched entries, clears the stored URL if it no longer matches
    the current quarter/year (catches stale URLs from a previous wrong calculation).
    """
    for entry in registry["entries"]:
        report_date_str = entry.get("report_date")
        if not report_date_str:
            continue
        try:
            d = date.fromisoformat(report_date_str.replace("/", "-"))
            new_q, new_y = find_fiscal_quarter(d, fy_end_month)
            entry["quarter"] = new_q
            entry["year"] = new_y
            if entry.get("status") != "fetched":
                url = entry.get("url") or ""
                company_slug = registry.get("company_slug", "")
                if f"q{new_q}-{new_y}" not in url or (company_slug and company_slug not in url):
                    entry["url"] = None
                    entry.pop("error", None)
                    if entry.get("status") == "error":
                        entry["status"] = "pending"
        except ValueError:
            pass


def cmd_init(args) -> None:
    """Bootstrap (or update) a ticker's registry."""
    ticker = args.ticker.upper()
    company_slug = args.company_slug.lower()
    earliest_year = args.from_year
    fy_end_month = args.fy_end_month
    from_date = date.fromisoformat(args.from_date) if args.from_date else None

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    dates = refresh_earnings_dates(ticker)

    registry = load_ticker_registry(ticker)
    if registry is None:
        registry = new_registry(ticker, company_slug, earliest_year, fy_end_month)
    else:
        registry["company_slug"] = company_slug
        registry["earliest_year"] = earliest_year
        registry["fy_end_month"] = fy_end_month
        _recalculate_quarters(registry, fy_end_month)

    added = queue_new_dates(registry, dates, from_date)
    resolved = resolve_pending_urls(registry)
    save_ticker_registry(ticker, registry)
    print(
        f"\nearliest_year={earliest_year}, fy_end_month={fy_end_month}, "
        f"{added} new entr{'y' if added == 1 else 'ies'} added, "
        f"{resolved} URL{'s' if resolved != 1 else ''} resolved -> {registry_path(ticker)}"
    )


def cmd_sync(args) -> None:
    """Discover new earnings dates per ticker (bounded by earliest_year) and fetch pending."""
    tickers = [args.ticker.upper()] if args.ticker else all_registered_tickers()
    if not tickers:
        print("No tickers registered. Run 'init <ticker> <slug> --from-year YYYY' first.")
        return

    grand_ok = grand_failed = 0
    for ticker in tickers:
        registry = load_ticker_registry(ticker)
        if registry is None:
            print(f"{ticker}: no registry (run 'init {ticker} <slug> --from-year YYYY' first).")
            continue

        print(f"\n=== {ticker} ({registry['company_slug']}) earliest_year={registry['earliest_year']} ===")

        dates = refresh_earnings_dates(ticker)
        if queue_new_dates(registry, dates) == 0:
            print("  No new earnings dates.")

        if args.retry:
            retried = 0
            for e in registry["entries"]:
                if e.get("status") == "error":
                    e["status"] = "pending"
                    e.pop("error", None)
                    retried += 1
                    print(f"  Retrying {ticker} Q{e['quarter']} FY{e['year']}")
            if retried == 0:
                print("  No errored entries to retry.")

        save_ticker_registry(ticker, registry)
        ok, failed = fetch_pending(registry)
        if ok or failed:
            save_ticker_registry(ticker, registry)
            print(f"  {ticker}: {ok} fetched, {failed} failed.")
        else:
            print(f"  {ticker}: nothing pending.")
        grand_ok += ok
        grand_failed += failed

    if len(tickers) > 1:
        print(f"\nTotal: {grand_ok} fetched, {grand_failed} failed across {len(tickers)} tickers.")


def cmd_fetch(_args) -> None:
    """Download pending entries across all tickers (no discovery)."""
    tickers = all_registered_tickers()
    if not tickers:
        print("No registry files found.")
        return

    touched = False
    for ticker in tickers:
        registry = load_ticker_registry(ticker)
        if registry is None:
            continue
        ok, failed = fetch_pending(registry)
        if ok or failed:
            touched = True
            save_ticker_registry(ticker, registry)

    if not touched:
        print("Nothing to fetch.")


def cmd_add(args) -> None:
    """Manually queue a single fiscal quarter for an already-registered ticker."""
    ticker = args.ticker.upper()
    registry = load_ticker_registry(ticker)
    if registry is None:
        print(
            f"No registry for {ticker}. "
            f"Run 'init {ticker} <slug> --from-year YYYY' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    for e in registry["entries"]:
        if e["quarter"] == args.quarter and e["year"] == args.year:
            print(f"Entry already exists for {ticker} Q{args.quarter} FY{args.year}.")
            return

    entry: dict = {"quarter": args.quarter, "year": args.year, "status": "pending", "url": args.url}
    registry["entries"].append(entry)
    save_ticker_registry(ticker, registry)
    print(f"Added {ticker} Q{args.quarter} FY{args.year} -> {registry_path(ticker)}")


def cmd_list(_args) -> None:
    tickers = all_registered_tickers()
    if not tickers:
        print("No registry files found.")
        return
    print(f"{'TICKER':<8} {'Q':<4} {'YEAR':<6} {'STATUS':<10} {'FILE'}")
    print("-" * 60)
    for ticker in tickers:
        registry = load_ticker_registry(ticker)
        if registry is None:
            continue
        for e in registry["entries"]:
            path = transcript_path(ticker, e)
            file_info = path.name if path.exists() else "-"
            print(f"{ticker:<8} {e['quarter']:<4} {e['year']:<6} {e['status']:<10} {file_info}")
            if e.get("error"):
                print(f"  error: {e['error']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m transcript_service",
        description="Earnings transcript downloader",
    )
    sub = parser.add_subparsers(dest="command")

    sync_p = sub.add_parser("sync", help="Discover new dates + fetch pending (default)")
    sync_p.add_argument("ticker", nargs="?", help="Restrict to one ticker (default: all)")
    sync_p.add_argument("--retry", action="store_true",
                        help="Also re-attempt entries with status=error")

    init_p = sub.add_parser("init", help="Bootstrap a ticker's registry")
    init_p.add_argument("ticker", help="Stock ticker, e.g. PATH")
    init_p.add_argument("company_slug", help="Motley Fool URL slug, e.g. uipath")
    init_p.add_argument("--from-year", dest="from_year", type=int, required=True, metavar="YYYY",
                        help="Earliest calendar year of report dates to include (stored as the registry floor)")
    init_p.add_argument("--fy-end-month", dest="fy_end_month", type=int, default=12, metavar="M",
                        help="Fiscal year end month 1-12 (default: 12 for December)")
    init_p.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD",
                        help="Optional finer date filter for the initial queue")

    sub.add_parser("fetch", help="Download pending transcripts only (no discovery)")

    add_p = sub.add_parser("add", help="Queue one fiscal quarter for a registered ticker")
    add_p.add_argument("ticker", help="Stock ticker, e.g. PATH")
    add_p.add_argument("quarter", type=int, help="Fiscal quarter (1-4)")
    add_p.add_argument("year", type=int, help="Fiscal year, e.g. 2025")
    add_p.add_argument("--url", help="Override the auto-constructed Motley Fool URL")

    sub.add_parser("list", help="Show registry status")

    args = parser.parse_args()

    if args.command is None:
        args.command = "sync"
        args.ticker = None
        args.retry = False

    {"init": cmd_init, "sync": cmd_sync, "fetch": cmd_fetch,
     "add": cmd_add, "list": cmd_list}[args.command](args)