"""Fiscal calendar helpers."""
import calendar
from datetime import date, timedelta


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


