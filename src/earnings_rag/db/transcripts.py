"""Queries against the transcripts and transcript_chunks tables."""
import logging
from datetime import date

import psycopg

from .connection import connection

logger = logging.getLogger(__name__)


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
    logger.info("Upserting transcript %s Q%d FY%d", ticker, quarter, fiscal_year)
    try:
        with connection() as conn:
            row = conn.execute(sql, (ticker, quarter, fiscal_year, report_date, content)).fetchone()
    except psycopg.Error:
        logger.exception("Failed to upsert transcript %s Q%d FY%d", ticker, quarter, fiscal_year)
        raise
    logger.info(
        "Upserted transcript %s Q%d FY%d (id=%s)", ticker, quarter, fiscal_year, row.get("id")
    )
    return row


def get_transcript(ticker: str, quarter: int, fiscal_year: int) -> dict | None:
    sql = """
        SELECT * FROM transcripts
        WHERE ticker = %s AND quarter = %s AND fiscal_year = %s
    """
    logger.debug("Fetching transcript %s Q%d FY%d", ticker, quarter, fiscal_year)
    try:
        with connection() as conn:
            row = conn.execute(sql, (ticker, quarter, fiscal_year)).fetchone()
    except psycopg.Error:
        logger.exception("Failed to fetch transcript %s Q%d FY%d", ticker, quarter, fiscal_year)
        raise
    if row is None:
        logger.debug("No transcript found for %s Q%d FY%d", ticker, quarter, fiscal_year)
    return row


def get_transcripts_by_ticker(ticker: str) -> list[dict]:
    sql = """
        SELECT * FROM transcripts
        WHERE ticker = %s
        ORDER BY fiscal_year, quarter
    """
    logger.info("Fetching transcripts for ticker %s", ticker)
    try:
        with connection() as conn:
            rows = conn.execute(sql, (ticker,)).fetchall()
    except psycopg.Error:
        logger.exception("Failed to fetch transcripts for ticker %s", ticker)
        raise
    logger.info("Fetched %d transcripts for ticker %s", len(rows), ticker)
    return rows


def get_all_transcripts() -> list[dict]:
    sql = """
        SELECT * FROM transcripts
        ORDER BY ticker, fiscal_year, quarter
    """
    logger.info("Fetching all transcripts from DB")
    try:
        with connection() as conn:
            rows = conn.execute(sql).fetchall()
    except psycopg.Error:
        logger.exception("Failed to fetch transcripts from DB")
        raise
    logger.info("Fetched %d transcripts from DB", len(rows))
    return rows


def upsert_transcript_chunks(
    transcript_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    sql = """
        INSERT INTO transcript_chunks (transcript_id, chunk_index, content, embedding)
        VALUES (%s, %s, %s, %s::vector)
        ON CONFLICT (transcript_id, chunk_index)
        DO UPDATE SET
            content   = EXCLUDED.content,
            embedding = EXCLUDED.embedding
    """
    # str([0.1, -0.2, 0.3]) -> "[0.1, -0.2, 0.3]"; pgvector's ::vector cast
    # accepts the whitespace, so no custom formatting is needed.
    rows = [
        (transcript_id, i, chunk, str(embedding))
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
    ]
    logger.info("Upserting %d chunks for transcript_id=%s", len(rows), transcript_id)
    try:
        with connection() as conn:
            conn.cursor().executemany(sql, rows)
    except psycopg.Error:
        logger.exception("Failed to upsert chunks for transcript_id=%s", transcript_id)
        raise
    logger.info("Upserted %d chunks for transcript_id=%s", len(rows), transcript_id)
