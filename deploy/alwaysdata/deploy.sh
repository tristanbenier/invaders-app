#!/usr/bin/env bash
# Update the alwaysdata site to the latest commit of main. Run over SSH:
#   ~/invaders/deploy/alwaysdata/deploy.sh
set -euo pipefail

APP_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$APP_DIR"

echo "==> Fetching code"
git pull --ff-only

echo "==> Backend dependencies"
backend/.venv/bin/pip install --quiet -r backend/requirements.txt

# The Vue app is built on the developer machine and committed (frontend/dist).
if [ ! -f frontend/dist/bundle.min.js ]; then
  echo "frontend/dist is missing: run \`make build\` locally and commit it." >&2
  exit 1
fi

echo "==> Database migrations and static files"
cd backend
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput --clear
.venv/bin/python manage.py check --deploy

echo "==> Reloading"
PIDFILE=gunicorn.pid
if [ -f "$PIDFILE" ] && pid=$(cat "$PIDFILE") && ps -p "$pid" -o args= 2>/dev/null | grep -q gunicorn; then
  # Gunicorn replaces its workers gracefully: they load the new code and .env.
  kill -HUP "$pid"
  echo "Done: Gunicorn reloaded."
else
  # alwaysdata stops idle sites: the next request starts the new code.
  echo "Done: the site is not running, the next visit starts the new version."
fi
