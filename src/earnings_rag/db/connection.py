"""PostgreSQL connection handling."""
import logging
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from ..config import postgres_dsn, postgres_target

logger = logging.getLogger(__name__)


@contextmanager
def connection():
    """Yield a fresh psycopg connection with dict rows, committed on exit."""
    target = postgres_target()
    logger.debug("Opening DB connection to %s", target)
    try:
        with psycopg.connect(postgres_dsn(), row_factory=dict_row) as conn:
            yield conn
    except psycopg.Error:
        logger.exception("DB connection to %s failed", target)
        raise
