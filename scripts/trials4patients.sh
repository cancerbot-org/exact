#!/usr/bin/env bash
# Local end-to-end test: connect to external trials DB + local ctomop patients
#
# Matches patients directly via the EXACT ORM — no web server required.
#
# Prerequisites:
#   1. exact local DB: migrated (python manage.py migrate)
#   2. Remote trials DB: accessible, contains trials in exact's schema
#   3. Local/remote ctomop DB: contains patient_info records
#
# Required env vars (set in .env or export manually):
#   TRIALS_DATABASE_URL  — remote trials database
#   PATIENT_DATABASE_URL  — ctomop patient database
#
# Options:
#   PERSON_IDS=1,2,3           — specific person IDs to test (default: all)

set -e

# Load environment variables from .env if present
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
if [ -f "$ROOT_DIR/.env" ]; then
  set -o allexport
  # shellcheck source=../.env
  source "$ROOT_DIR/.env"
  set +o allexport
fi

PATIENT_DB="${PATIENT_DATABASE_URL:-}"
PERSON_IDS="${PERSON_IDS:-}"

# ── Validate ──────────────────────────────────────────────────────────
if [ -z "$PATIENT_DATABASE_URL" ]; then
  echo "ERROR: Set PATIENT_DATABASE_URL to point at your ctomop PostgreSQL DB." >&2
  echo "  export PATIENT_DATABASE_URL=postgresql://user:pass@localhost:5432/ctomop" >&2
  exit 1
fi

if [ -z "$TRIALS_DATABASE_URL" ]; then
  echo "ERROR: Set TRIALS_DATABASE_URL for the remote trials DB." >&2
  echo "  export TRIALS_DATABASE_URL=postgresql://user:pass@host:5432/dbname" >&2
  exit 1
fi

echo "=============================================="
echo "Step 1: Verify connectivity"
echo "=============================================="
echo "  Trials DB: $TRIALS_DATABASE_URL"
echo "  Patient DB: $PATIENT_DATABASE_URL"

TRIAL_COUNT=$(python manage.py shell -c "
from trials.models import Trial
count = Trial.objects.count()
print(count)
" 2>/dev/null | tail -1)
echo "  Trials available: $TRIAL_COUNT"

if [ "$TRIAL_COUNT" = "0" ]; then
  echo "ERROR: No trials found in the remote database. Check TRIALS_DATABASE_URL." >&2
  exit 1
fi

echo ""
echo "=============================================="
echo "Step 2: Run search for ctomop patients (direct DB)"
echo "=============================================="
SEARCH_ARGS=(
  --source-db-url "$PATIENT_DATABASE_URL"
  --limit 20
  --output /tmp/exact_local_test_results.json
)

if [ -n "$PERSON_IDS" ]; then
  SEARCH_ARGS+=(--person-ids "$PERSON_IDS")
fi

python manage.py search_trials_for_ctomop_patients "${SEARCH_ARGS[@]}"

echo ""
echo "=============================================="
echo "Step 3: Summary"
echo "=============================================="
python manage.py shell -c "
import json
with open('/tmp/exact_local_test_results.json') as f:
    results = json.load(f)
print(f'  Patients searched : {len(results)}')
for r in results:
    pid = r['person_id']
    disease = r.get('disease') or '?'
    total = r['total_trials']
    eligible = r['eligible_count']
    potential = r['potential_count']
    score = r.get('best_match_score')
    score_str = f\"{score}%\" if score else 'n/a'
    print(f'  person_id={pid} [{disease}] → {total} trials | {eligible} eligible | {potential} potential | best: {score_str}')
" 2>/dev/null

echo ""
echo "Full results written to /tmp/exact_local_test_results.json"
