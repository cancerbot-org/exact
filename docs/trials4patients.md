# Trials for Patients — End-to-End Testing

## Prerequisites

- EXACT local DB created and migrated (`python manage.py migrate`)
- `TRIALS_DATABASE_URL` — remote trials database
- `PATIENT_DATABASE_URL` — patient database with `patient_info` records

## Run the full test

From the `exact/` directory:

```bash
export TRIALS_DATABASE_URL=postgresql://user:pass@host:5432/trials
export PATIENT_DATABASE_URL=postgresql://user:pass@host:5432/patients

bash scripts/trials4patients.sh
```

The script runs all steps automatically:

| Step | What happens |
|------|-------------|
| 1 | Verifies connectivity to both databases |
| 2 | Runs `search_trials_for_patients` for all patients |
| 3 | Prints a per-patient summary; full JSON written to `/tmp/exact_local_test_results.json` |

Override defaults if needed:

```bash
# Run for specific patients only
PERSON_IDS=1,2,3 bash scripts/trials4patients.sh

# Run for the first 50 patients (ordered by person_id)
PATIENT_LIMIT=50 bash scripts/trials4patients.sh
```

## Run manually

```bash
cd /path/to/exact

# Specific patients
python manage.py search_trials_for_patients \
  --source-db-url "$PATIENT_DATABASE_URL" \
  --person-ids "9001,9002,9003" \
  --limit 20 \
  --output /tmp/results.json

# Top N patients (ordered by person_id)
python manage.py search_trials_for_patients \
  --source-db-url "$PATIENT_DATABASE_URL" \
  --patient-limit 50 \
  --limit 20 \
  --output /tmp/results.json
```

The command reads patients directly from the patient database and matches
them against trials using the EXACT ORM — no web server required.

## Standalone local testing (no remote databases)

For fully self-contained local testing without external databases:

```bash
python manage.py migrate
python manage.py seed_reference_data
python manage.py seed_test_trials
python manage.py runserver
```

This creates 8 test trials (2 per disease) — see [setup.md](setup.md#5-seed-reference-data) for the full list.

Then run a match against the seeded trials using curl:

```bash
# Create a token first if you haven't already:
python manage.py drf_create_token <username>

# Search for trials matching a relapsed myeloma patient:
curl -s http://localhost:8000/trials/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"patientInfo": {"disease": "multiple myeloma", "patientAge": 65, "priorTherapy": "One line"}}' \
  | python -m json.tool
```

Or use the Django shell for direct ORM access (no web server needed):

```bash
python manage.py shell <<'EOF'
from trials.models import Trial
from trials.services.patient_info.resolve import resolve_patient_info

pi = resolve_patient_info({"disease": "multiple myeloma", "patientAge": 65, "priorTherapy": "One line"})
from trials.querysets.trial import TrialQuerySet
qs = Trial.objects.filter_for_patient(pi)
for t in qs[:5]:
    print(t.study_id, t.match_score)
EOF
```

To wipe and re-seed:

```bash
python manage.py seed_test_trials --clear
```

## Expected output

```
  person_id=9001 [multiple myeloma]         → 2 trials | 1 eligible | 1 potential | best: 88%
  person_id=9002 [multiple myeloma]         → 1 trial  | 1 eligible | 0 potential | best: 92%
  ...

Done. Patients processed: 7, Errors: 0
```

Exact scores will vary. If a patient returns 0 trials, check:

1. `seed_reference_data` was run (or the trials DB has reference data)
2. Disease strings match (case-insensitive comparison is handled by the engine)

## Cleaning up

```bash
# Remove test trials (standalone mode only)
python manage.py seed_test_trials --clear
```

---

## Comparing EXACT results against CancerBot

`compare_trials` runs EXACT matching for a list of named patients and
compares the top-N ranked trials against stored CancerBot trial IDs.

```bash
python manage.py compare_trials \
  --input scripts/compare_input.json \
  --output /tmp/compare_results \
  --source-db-url "$PATIENT_DATABASE_URL" \
  --top-n 5
```

`compare_input.json` is a JSON array where each entry has:

| Field | Description |
|-------|-------------|
| `name` | Patient full name (for DB lookup) |
| `email` | Patient email (used for DB lookup if available) |
| `person_id` | Optional explicit person_id (highest-priority lookup) |
| `zipcode` | Patient zip code (used for distance scoring — takes priority over DB value) |
| `country_code` | Patient country code (default `US`) |
| `cancerbot_trial_ids` | List of CancerBot top-N trial IDs to compare against |

### Zip code priority

The command resolves the patient's zip code in this order:
1. `zipcode` field in `compare_input.json` (highest priority — kept current by `refresh_cb_trial_ids.py`)
2. `postalCode` from `cancerbot_patients_data.json` (CB live data cache)
3. `postal_code` column in the patient DB (lowest priority — may be stale)

A warning is printed when the JSON zip differs from the DB value:
```
[zip override] JSON=02169/US  DB=02468  — using JSON zip for distance scoring
```

### Refreshing stored CancerBot trial IDs and zip codes

```bash
# Show diffs between stored and live CB data
python scripts/refresh_cb_trial_ids.py

# Update compare_input.json with live trial IDs and zip codes
python scripts/refresh_cb_trial_ids.py --update
```

Zip-code changes are highlighted in bold yellow in the terminal output.

### `--explain` flag

Pass `--explain` to print a per-attribute breakdown for every row where
`type(E) != type(CB)` (eligible vs potential, or vice-versa):

```bash
python manage.py compare_trials \
  --input scripts/compare_input.json \
  --output /tmp/compare_results \
  --source-db-url "$PATIENT_DATABASE_URL" \
  --top-n 5 \
  --explain
```

For each mismatched trial the command prints:
- EXACT's per-attribute statuses (`matched` / `unknown` / `not_matched`) from `TrialMatchExplainer`
- CB's `attributesToFillIn` (attributes the patient hasn't filled in on CB) from the cached search data

### Output

Three files are written per run:

| File | Contents |
|------|----------|
| `{output}.json` | Per-patient comparison with overlap analysis, scores, ineligibility reasons |
| `{output}.txt` | One line per patient: `name<TAB>exact_id1, exact_id2, ...` |
| `{output}.log` | Plain-text copy of terminal output (ANSI codes stripped) |

---

## Per-attribute match explanation for a patient+trial pair

`explain_trial_match` shows the per-attribute match status for a specific
patient+trial pair side-by-side from two sources: CTOMOP (EXACT's view) and
`cancerbot_patients_data.json` (CancerBot's view). Useful for diagnosing
eligible/potential or ranking discrepancies.

```bash
python manage.py explain_trial_match \
  --person-id 20494 \
  --trial-id 18141 \
  --source-db-url "$PATIENT_DATABASE_URL"

# With explicit patient name to match the CB data entry:
python manage.py explain_trial_match \
  --person-id 20494 \
  --name "Charlotte Walker" \
  --trial-id 18141 \
  --source-db-url "$PATIENT_DATABASE_URL" \
  --cb-data scripts/cancerbot_patients_data.json
```

Output: a table with one row per eligibility criterion showing `attr`,
`status` (matched / unknown / not_matched), the CTOMOP patient value, and
the CB patient value — making data gaps between the two sources immediately
visible.

---

## Probing trial eligibility for a specific patient

`probe_eligibility` explains why a trial is eligible or ineligible for a
specific patient. Useful for debugging mismatches.

```bash
python manage.py probe_eligibility \
  --person-id 20300 \
  --trial-id 18502 \
  --source-db-url "$PATIENT_DATABASE_URL"
```

Output:

```
=== Hannah Anderson (person_id=20300) ===
  geo_point           : POINT (-71.0549 42.3601)
  prior_therapy       : 'One line'
  her2_status         : 'her2_minus'
  estrogen_receptor   : 'er_plus_with_hi_exp'
  ...

Trial 18502 → ELIGIBLE (passes all filters)
```

If the trial is ineligible, all dropped filter attributes are listed:

```
Trial 42005 → INELIGIBLE. Dropped by:
  therapies_required                         val=[]  dropped=1
```

> **Note**: The command uses `psql` subprocess (not a direct psycopg2 connection)
> to avoid a double-free crash on macOS/conda when a second DB connection is
> opened while Django's own connection is active.
