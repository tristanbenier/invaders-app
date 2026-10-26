#!/usr/bin/env bash
# Command of the alwaysdata "User program" site (see README.md): starts Gunicorn on the IP and
# PORT that alwaysdata gives the site. The rest of the configuration is in the root .env.
set -euo pipefail

APP_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$APP_DIR/backend"

# One process with threads: the account has 256 MB of RAM (about 90 MB per Django process),
# and threads keep serving while a map tile waits on OpenStreetMap.
export GUNICORN_BIND="[${IP:-::}]:${PORT:?PORT is set by alwaysdata}"
export GUNICORN_WORKERS=1
export GUNICORN_THREADS=4
export GUNICORN_PIDFILE="$APP_DIR/backend/gunicorn.pid"
# Requests only reach the site through alwaysdata's proxy, which sets X-Forwarded-Proto.
export GUNICORN_FORWARDED_ALLOW_IPS="*"

exec .venv/bin/gunicorn -c gunicorn.conf.py
