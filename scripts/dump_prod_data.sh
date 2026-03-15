#!/usr/bin/env bash
# Run this in the SOURCE (cancerbot) project to dump trial data.
# Copy the resulting JSON files to the exact project and run load_prod_data.sh.
set -e

OUT=dump_$(date +%Y%m%d)
mkdir -p "$OUT"

echo "Dumping reference data..."
python manage.py dumpdata \
  trials.Country \
  trials.State \
  trials.Disease \
  trials.TherapyComponent \
  trials.Therapy \
  trials.TherapyRound \
  trials.MarkerCategory \
  trials.Marker \
  trials.TrialType \
  trials.TrialTypeDiseaseConnection \
  trials.DiseaseRoundTherapyConnection \
  --indent 2 > "$OUT/reference.json"



echo ""
echo "Done. Files written to $OUT/"
echo ""
echo "To load in the exact project (in order):"
echo "  python manage.py loaddata $OUT/reference.json"

