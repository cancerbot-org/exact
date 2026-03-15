#!/usr/bin/env bash
# Load trial data dumped from the source project.
# Usage: bash scripts/load_prod_data.sh path/to/dump_YYYYMMDD/
set -e

DIR="${1:?Usage: $0 <dump-dir>}"

echo "Step 1: Seed static reference data..."
python manage.py seed_reference_data

echo "Step 2: Load prod reference data (diseases, therapies, markers, trial types)..."
python manage.py loaddata "$DIR/reference.json"

echo "Done."
