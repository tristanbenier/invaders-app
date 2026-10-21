#!/usr/bin/env bash
# Update the production server to the latest commit of main.
# Run by the admin user (with sudo rights) from anywhere: /srv/invaders/deploy/deploy.sh
set -euo pipefail

APP_DIR=/srv/invaders
as_app() { sudo -u invaders -H "$@"; }

echo "==> Fetching code"
as_app git -C "$APP_DIR" pull --ff-only

echo "==> Backend dependencies"
as_app "$APP_DIR/backend/.venv/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"

echo "==> Building the Vue app"
as_app npm --prefix "$APP_DIR/frontend" ci --no-audit --no-fund
as_app npm --prefix "$APP_DIR/frontend" run build

echo "==> Database migrations and static files"
cd "$APP_DIR/backend"
as_app .venv/bin/python manage.py migrate --noinput
as_app .venv/bin/python manage.py collectstatic --noinput --clear
as_app .venv/bin/python manage.py check --deploy

echo "==> Restarting"
sudo systemctl restart invaders
sleep 2
systemctl is-active --quiet invaders && echo "Done: invaders is running." || {
  echo "invaders failed to start, see: journalctl -u invaders -n 50" >&2
  exit 1
}
