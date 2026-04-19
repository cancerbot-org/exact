#!/usr/bin/env bash
# Compare two ethalon-format CSVs: ground truth vs EXACT results.
# No patient DB or trials DB connection required.
#
# Usage:
#   bash scripts/evaluator/evaluate.sh ethalon.csv results.csv
#   bash scripts/evaluator/evaluate.sh ethalon.csv results.csv --output comparison.json

set -e

export MALLOC_NANO_ZONE=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$ROOT_DIR/.env" ]; then
  set -o allexport
  source "$ROOT_DIR/.env"
  set +o allexport
fi

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: bash scripts/evaluator/evaluate.sh ethalon.csv results.csv [--output out.json]" >&2
  exit 1
fi

ETHALON="$1"
RESULTS="$2"
shift 2

python manage.py evaluate_ethalon \
  --ethalon "$ETHALON" \
  --results "$RESULTS" \
  "$@"
