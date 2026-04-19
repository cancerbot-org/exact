#!/usr/bin/env bash
# Initialize the trials database from a gzipped SQL backup when empty.
#
# Behavior:
#   - Skip if TRIALS_DATABASE_URL is not set (single-DB deployments).
#   - Skip if TRIALS_DATABASE_INIT_FROM_BACKUP is not truthy (opt-in only,
#     because this step DROPs the public schema before restoring).
#   - Skip if trials_trial already has rows.
#   - Otherwise download TRIALS_DATABASE_BACKUP_URL (default: public GCS bucket)
#     and restore it into TRIALS_DATABASE_URL.
set -euo pipefail

TRIALS_DATABASE_URL="${TRIALS_DATABASE_URL:-}"
TRIALS_DATABASE_BACKUP_URL="${TRIALS_DATABASE_BACKUP_URL:-https://storage.googleapis.com/cancerbot-public/exact/trials/latest.sql.gz}"
TRIALS_DATABASE_INIT_FROM_BACKUP="${TRIALS_DATABASE_INIT_FROM_BACKUP:-}"

log() { echo "[init_trials_db] $*"; }

if [ -z "$TRIALS_DATABASE_URL" ]; then
    log "TRIALS_DATABASE_URL not set — skipping."
    exit 0
fi

case "${TRIALS_DATABASE_INIT_FROM_BACKUP,,}" in
    1|true|yes|on) ;;
    *)
        log "TRIALS_DATABASE_INIT_FROM_BACKUP not enabled — skipping."
        log "Set TRIALS_DATABASE_INIT_FROM_BACKUP=1 to auto-restore the trials DB from a snapshot."
        exit 0
        ;;
esac

log "Checking trials database status..."
row_count="$(psql "$TRIALS_DATABASE_URL" -tAXc \
    'SELECT COUNT(*) FROM trials_trial' 2>/dev/null || true)"
row_count="${row_count//[[:space:]]/}"

if [[ "$row_count" =~ ^[0-9]+$ ]] && [ "$row_count" -gt 0 ]; then
    log "trials_trial already populated (${row_count} rows) — skipping restore."
    exit 0
fi

log "trials_trial is empty or missing — restoring from backup."
log "Backup source: $TRIALS_DATABASE_BACKUP_URL"

backup_file="$(mktemp --suffix=.sql.gz)"
trap 'rm -f "$backup_file"' EXIT

python3 - "$TRIALS_DATABASE_BACKUP_URL" "$backup_file" <<'PY'
import shutil
import sys
import urllib.request

url, dest = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(url, timeout=30) as resp, open(dest, "wb") as out:
    shutil.copyfileobj(resp, out, length=1024 * 1024)
PY

log "Backup downloaded ($(du -h "$backup_file" | cut -f1)). Recreating public schema..."
psql "$TRIALS_DATABASE_URL" -v ON_ERROR_STOP=1 -c \
    'DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;'

log "Restoring backup into trials database..."
gunzip -c "$backup_file" | psql "$TRIALS_DATABASE_URL" -v ON_ERROR_STOP=1 -q

log "Done."
