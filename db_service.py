import os
from contextlib import contextmanager
from datetime import date

import psycopg
from psycopg.rows import dict_row


def _dsn() -> str:
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB', 'earnings')} "
        f"user={os.getenv('POSTGRES_USER', 'postgres')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'postgres')}"
    )


@contextmanager
def _conn():
    with psycopg.connect(_dsn(), row_factory=dict_row) as conn:
        yield conn


def upsert_transcript(
    ticker: str,
    quarter: int,
    fiscal_year: int,
    report_date: date,
    content: str,
) -> dict:
    sql = """
        INSERT INTO transcripts (ticker, quarter, fiscal_year, report_date, content)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (ticker, quarter, fiscal_year)
        DO UPDATE SET
            report_date  = EXCLUDED.report_date,
            content      = EXCLUDED.content,
            updated_at   = now()
        RETURNING *
    """
    with _conn() as conn:
        row = conn.execute(sql, (ticker, quarter, fiscal_year, report_date, content)).fetchone()
    return row


def get_transcript(ticker: str, quarter: int, fiscal_year: int) -> dict | None:
    sql = """
        SELECT * FROM transcripts
        WHERE ticker = %s AND quarter = %s AND fiscal_year = %s
    """
    with _conn() as conn:
        return conn.execute(sql, (ticker, quarter, fiscal_year)).fetchone()


def get_transcripts_by_ticker(ticker: str) -> list[dict]:
    sql = """
        SELECT * FROM transcripts
        WHERE ticker = %s
        ORDER BY fiscal_year, quarter
    """
    with _conn() as conn:
        return conn.execute(sql, (ticker,)).fetchall()
