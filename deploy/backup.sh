#!/usr/bin/env bash
# Nightly backup of the SQLite database and uploaded photos, kept for KEEP_DAYS.
# Run by invaders-backup.timer as the invaders user.
set -euo pipefail

APP_DIR=/srv/invaders
BACKUP_DIR=/srv/invaders-backups
KEEP_DAYS=14
STAMP=$(date +%Y%m%d-%H%M)

mkdir -p "$BACKUP_DIR"

# SQLite online backup API: a consistent copy even while the app is writing.
"$APP_DIR/backend/.venv/bin/python" - "$APP_DIR/backend/db.sqlite3" "$BACKUP_DIR/db-$STAMP.sqlite3" <<'PY'
import sqlite3, sys
source, target = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
with target:
    source.backup(target)
source.close()
target.close()
PY
gzip "$BACKUP_DIR/db-$STAMP.sqlite3"

if [ -d "$APP_DIR/backend/media" ]; then
  tar -czf "$BACKUP_DIR/media-$STAMP.tar.gz" -C "$APP_DIR/backend" media
fi

find "$BACKUP_DIR" -name 'db-*.sqlite3.gz' -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name 'media-*.tar.gz' -mtime +"$KEEP_DAYS" -delete
echo "Backup $STAMP done."
