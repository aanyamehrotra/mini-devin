#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
npm ci --prefix frontend
npm run build --prefix frontend
printf '\nSetup complete. Configure the private .env, start Docker, then run scripts/start-local.sh\n'
