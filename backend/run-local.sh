#!/usr/bin/env bash
# Run the backend locally (no Docker).
# - Uses SQLite (the .env DATABASE_URL points at the Docker "db" host).
# - Watches ONLY the app/ folder so writes to talenttrail.db / .chroma don't
#   trigger a reload mid-request (which shows up as CORS/network errors).
set -euo pipefail
cd "$(dirname "$0")"

source .venv/bin/activate

export DATABASE_URL="sqlite:///./talenttrail.db"
export JOB_API_VERIFY_SSL="${JOB_API_VERIFY_SSL:-false}"

exec uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
