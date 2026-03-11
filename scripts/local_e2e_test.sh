#!/usr/bin/env bash
# Local end-to-end test: seed fake data → start exact API → run trial search
#
# Prerequisites:
#   1. exact:  PostgreSQL DB running + migrated  (python manage.py migrate)
#   2. ctomop: PostgreSQL DB running + migrated
#              export DATABASE_URL=postgresql://user:pass@localhost:5432/ctomop
#              cd /path/to/ctomop && python manage.py migrate
#
# Usage (from the exact/ directory):
#   export CTOMOP_DATABASE_URL=postgresql://user:pass@localhost:5432/ctomop
#   bash scripts/local_e2e_test.sh
#
# Override the exact API URL and port if needed:
#   EXACT_PORT=9000 bash scripts/local_e2e_test.sh

set -e

CTOMOP_DB="${CTOMOP_DATABASE_URL:-}"
EXACT_PORT="${EXACT_PORT:-8000}"
EXACT_URL="http://localhost:${EXACT_PORT}"
CTOMOP_DIR="${CTOMOP_DIR:-../ctomop}"

# ── Validate ──────────────────────────────────────────────────────────
if [ -z "$CTOMOP_DB" ]; then
  echo "ERROR: Set CTOMOP_DATABASE_URL to point at your local ctomop PostgreSQL DB." >&2
  echo "  export CTOMOP_DATABASE_URL=postgresql://user:pass@localhost:5432/ctomop" >&2
  exit 1
fi

if [ ! -f "$CTOMOP_DIR/manage.py" ]; then
  echo "ERROR: ctomop not found at $CTOMOP_DIR — set CTOMOP_DIR env var." >&2
  exit 1
fi

echo "=============================================="
echo "Step 1: Seed exact reference data + test trials"
echo "=============================================="
python manage.py seed_reference_data
python manage.py seed_test_trials
python manage.py shell -c "
from trials.models import Trial
count = Trial.objects.filter(code__startswith='TEST-').count()
print(f'  {count} TEST-* trials ready in exact')
"

echo ""
echo "=============================================="
echo "Step 2: Seed test patients in ctomop"
echo "=============================================="
(cd "$CTOMOP_DIR" && DATABASE_URL="$CTOMOP_DB" python manage.py seed_test_patients)

echo ""
echo "=============================================="
echo "Step 3: Create an exact API token"
echo "=============================================="
# Create a dedicated test user + token if they don't exist yet
EXACT_TOKEN=$(python manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user, _ = User.objects.get_or_create(username='testrunner', defaults={'is_staff': False})
if not user.has_usable_password():
    user.set_password('testrunner')
    user.save()
token, _ = Token.objects.get_or_create(user=user)
print(token.key)
" 2>/dev/null | grep -E '^[a-f0-9]{40}$')
echo "  Token: $EXACT_TOKEN"

echo ""
echo "=============================================="
echo "Step 4: Start exact dev server (background)"
echo "=============================================="
python manage.py runserver "$EXACT_PORT" &
DJANGO_PID=$!
echo "  exact running on $EXACT_URL (PID $DJANGO_PID)"

# Wait for server to be ready
echo "  Waiting for server..."
for i in $(seq 1 20); do
  if curl -sf "$EXACT_URL/swagger/" -o /dev/null 2>/dev/null; then
    echo "  Server ready."
    break
  fi
  sleep 1
done

echo ""
echo "=============================================="
echo "Step 5: Run search for all test patients"
echo "=============================================="
python manage.py search_trials_for_ctomop_patients \
  --source-db-url "$CTOMOP_DB" \
  --api-url "$EXACT_URL" \
  --api-token "$EXACT_TOKEN" \
  --person-ids "9001,9002,9003,9004,9005,9006,9007" \
  --limit 20 \
  --sort matchScore \
  --output /tmp/exact_local_test_results.json

echo ""
echo "=============================================="
echo "Step 6: Summary"
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
echo ""
echo "Press Ctrl+C to stop the exact server."
wait $DJANGO_PID
