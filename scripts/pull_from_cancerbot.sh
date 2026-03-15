#!/usr/bin/env bash
# Pull trial catalog data from a CancerBot database into this local EXACT instance.
#
# Usage:
#   export CANCERBOT_DATABASE_URL=postgresql://user:pass@host:5432/cancerbot
#   bash scripts/pull_from_cancerbot.sh
#
# Or pass the URL directly:
#   bash scripts/pull_from_cancerbot.sh postgresql://user:pass@host:5432/cancerbot
#
# Steps:
#   1. Seed static reference data in EXACT (diseases, therapies, markers, trial types)
#   2. Run load_trials_from_cancerbot management command (Country → State → Location
#      → Trial → LocationTrial, with natural-key upserts and FK remapping)

set -e

SOURCE_URL="${1:-${CANCERBOT_DATABASE_URL:-}}"

if [ -z "$SOURCE_URL" ]; then
  echo "ERROR: No source DB URL." >&2
  echo "Usage: $0 <postgresql-url>" >&2
  echo "  or:  export CANCERBOT_DATABASE_URL=... && $0" >&2
  exit 1
fi

echo "========================================"
echo "Step 1: Seed static reference data in EXACT"
echo "========================================"
python manage.py seed_reference_data

echo ""
echo "Done."
