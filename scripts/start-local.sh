#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  printf 'Run scripts/setup-local.sh first.\n' >&2
  exit 1
fi
.venv/bin/python -m app.tools.preflight
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "${MINI_DEVIN_PORT:-8000}" --workers 1
