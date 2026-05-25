#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
