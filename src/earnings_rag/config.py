"""Filesystem paths and environment-derived settings.

Every path and env var the application reads is resolved here, so the rest of
the package never touches ``os.environ`` or computes a path relative to its own
``__file__``.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = Path(os.getenv("EARNINGS_DATA_DIR", REPO_ROOT / "data"))
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
REGISTRY_DIR = DATA_DIR / "registry"
EARNINGS_DATES_DIR = DATA_DIR / "earnings_dates"

MIGRATIONS_DIR = REPO_ROOT / "migrations"

EVAL_RUNS_DIR = Path(os.getenv("EARNINGS_EVAL_DIR", REPO_ROOT / "eval_runs"))


def postgres_dsn() -> str:
    """libpq connection string built from POSTGRES_* env vars."""
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB', 'earnings')} "
        f"user={os.getenv('POSTGRES_USER', 'postgres')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'postgres')}"
    )


def postgres_target() -> str:
    """host:port/dbname, for log messages that shouldn't leak the password."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "earnings")
    return f"{host}:{port}/{dbname}"


def load_env() -> None:
    """Populate os.environ from a .env file at the repo root, if one exists."""
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")


def configure_logging() -> None:
    """Apply the package-wide logging format. Safe to call more than once."""
    import logging

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
