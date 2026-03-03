#!/usr/bin/env bash
# Run this in the SOURCE (biblum/cancerbot) project to dump trial data.
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

echo "Dumping locations..."
python manage.py dumpdata \
  trials.Location \
  --indent 2 > "$OUT/locations.json"

echo "Dumping trials..."
python manage.py dumpdata \
  trials.Trial \
  --indent 2 > "$OUT/trials.json"

echo "Dumping location-trial links..."
python manage.py dumpdata \
  trials.LocationTrial \
  --indent 2 > "$OUT/location_trials.json"

echo ""
echo "Done. Files written to $OUT/"
echo ""
echo "To load in the exact project (in order):"
echo "  python manage.py loaddata $OUT/reference.json"
echo "  python manage.py loaddata $OUT/locations.json"
echo "  python manage.py loaddata $OUT/trials.json"
echo "  python manage.py loaddata $OUT/location_trials.json"
