from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_MODULE_DIR = Path(__file__).resolve().parent

TRANSCRIPTS_DIR = REPO_ROOT / "output" / "transcripts"
TRANSCRIPTS_REGISTRY_DIR = _MODULE_DIR / "transcripts_registry"
EARNINGS_DATES_DIR = _MODULE_DIR / "earnings_dates"