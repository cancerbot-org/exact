#!/usr/bin/env bash
# Reproduce EXACT vs CancerBot comparison results in Docker.
#
# Prerequisites:
#   - Docker + Docker Compose installed
#   - .env file with TRIALS_DATABASE_URL and PATIENT_DATABASE_URL set
#     (copy .env.example to .env and fill in credentials)
#
# Usage:
#   bash scripts/reproduce.sh
#
# Output:
#   /tmp/compare_results.json   — full per-patient comparison (JSON)
#   /tmp/compare_results.txt    — EXACT top-5 per patient (text)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "ERROR: .env not found. Copy .env.example to .env and fill in DB credentials." >&2
  exit 1
fi

echo "=== Step 1: Build image ==="
docker compose build

echo ""
echo "=== Step 2: Run comparison ==="
docker compose run --rm \
  -e INPUT=scripts/compare_input.json \
  -e OUTPUT=/tmp/compare_results \
  -e TOP_N=5 \
  exact \
  bash scripts/compare_trials.sh

echo ""
echo "=== Done ==="
echo "Results:"
echo "  JSON: /tmp/compare_results.json"
echo "  TXT:  /tmp/compare_results.txt"
