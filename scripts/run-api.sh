#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

exec uv run uvicorn earnings_rag.api:app --host 0.0.0.0 --port 8000 --reload
