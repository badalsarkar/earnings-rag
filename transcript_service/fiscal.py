"""Fiscal calendar helpers backed by yfinance."""
import calendar
from datetime import date, timedelta

import yfinance as yf

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def fiscal_year_end_month(ticker: str) -> int:
    """Return the fiscal year end month (1-12) for a ticker via yfinance."""
    info = yf.Ticker(ticker).info
    name = info.get("fiscalYearEnd", "December")
    return _MONTH_NAMES.index(name) + 1


def quarter_end_date(fy_end_month: int, fiscal_year: int, quarter: int) -> date:
    """Return the last day of the given fiscal quarter."""
    month = fy_end_month
    year = fiscal_year
    for _ in range(4 - quarter):
        month -= 3
        if month <= 0:
            month += 12
            year -= 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def find_fiscal_quarter(report_date: date, fy_end_month: int) -> tuple[int, int]:
    """Return (quarter, fiscal_year) for an earnings call date.

    Searches fiscal years around the report date; earnings calls happen
    within 90 days after quarter end.
    """
    for fy in [report_date.year - 1, report_date.year, report_date.year + 1]:
        for q in range(1, 5):
            q_end = quarter_end_date(fy_end_month, fy, q)
            if q_end < report_date <= q_end + timedelta(days=90):
                return q, fy
    raise ValueError(f"Could not determine fiscal quarter for {report_date}")


def get_earnings_call_date(ticker: str, quarter: int, fiscal_year: int) -> str:
    """Return the earnings call date (YYYY/MM/DD) for a fiscal quarter via yfinance."""
    fy_end_month = fiscal_year_end_month(ticker)
    q_end = quarter_end_date(fy_end_month, fiscal_year, quarter)
    window_end = q_end + timedelta(days=90)

    earnings_df = yf.Ticker(ticker).earnings_dates
    if earnings_df is None or earnings_df.empty:
        raise ValueError(f"No earnings dates found for {ticker} via yfinance")

    for dt in sorted(earnings_df.index):
        d = dt.date() if hasattr(dt, "date") else dt
        if q_end < d <= window_end:
            return d.strftime("%Y/%m/%d")

    raise ValueError(
        f"No earnings call date found for {ticker} Q{quarter} FY{fiscal_year} "
        f"in window {q_end} – {window_end}."
    )