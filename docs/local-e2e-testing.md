# Local end-to-end testing

How to seed fake data and run a full trial search locally, without real patient data.

## Prerequisites

- exact PostgreSQL DB created and migrated (`python manage.py migrate`)
- ctomop PostgreSQL DB created and migrated (see below)
- Both projects checked out locally

## One-time ctomop setup

ctomop's migrations use PostgreSQL-specific SQL and will not run on SQLite.
Create a local PostgreSQL database for it once:

```bash
createdb ctomop_local

export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ctomop_local
cd /path/to/ctomop
python manage.py migrate
```

## Run the full test

From the `exact/` directory:

```bash
export PATIENT_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ctomop_local

bash scripts/local_e2e_test.sh
```

The script runs all steps automatically:

| Step | What happens |
|------|-------------|
| 1 | `seed_reference_data` — creates diseases, therapies, markers, trial types in exact |
| 2 | `seed_test_trials` — creates 8 fake trials (2 per disease) in exact |
| 3 | `seed_test_patients` — creates 7 fake patients in ctomop |
| 4 | Creates an exact API token for the `testrunner` user |
| 5 | Starts exact's dev server on port 8000 (background) |
| 6 | Runs `search_trials_for_ctomop_patients` for all 7 test patients |
| 7 | Prints a per-patient summary; full JSON written to `/tmp/exact_local_test_results.json` |

Override defaults if needed:

```bash
EXACT_PORT=9000 CTOMOP_DIR=../../ctomop bash scripts/local_e2e_test.sh
```

## Run steps individually

### exact — seed reference data and test trials

```bash
cd /path/to/exact

python manage.py seed_reference_data
python manage.py seed_test_trials

# Verify
python manage.py shell -c "
from trials.models import Trial
for t in Trial.objects.filter(code__startswith='TEST-'):
    print(t.code, '|', t.disease, '|', t.brief_title)
"
```

To wipe and re-seed:

```bash
python manage.py seed_test_trials --clear
```

### ctomop — seed test patients

```bash
cd /path/to/ctomop

DATABASE_URL=$PATIENT_DATABASE_URL python manage.py seed_test_patients

# Verify
DATABASE_URL=$PATIENT_DATABASE_URL python manage.py shell -c "
from omop_core.models import PatientInfo
for pi in PatientInfo.objects.filter(person_id__gte=9001):
    print(pi.person_id, '|', pi.disease, '|', 'age', pi.patient_age)
"
```

To wipe and re-seed:

```bash
DATABASE_URL=$PATIENT_DATABASE_URL python manage.py seed_test_patients --clear
```

### Run the search manually

```bash
cd /path/to/exact

# Get or create a token
python manage.py drf_create_token testrunner

python manage.py search_trials_for_ctomop_patients \
  --source-db-url "$PATIENT_DATABASE_URL" \
  --api-url http://localhost:8000 \
  --api-token <your-token> \
  --person-ids "9001,9002,9003,9004,9005,9006,9007" \
  --limit 20 \
  --sort matchScore \
  --output /tmp/results.json
```

## Fake data reference

### Test trials in exact (8 total)

| Code | Disease | Scenario |
|------|---------|----------|
| `TEST-MM-001` | Multiple myeloma | R/R MM — ≥1 prior line required |
| `TEST-MM-002` | Multiple myeloma | Newly diagnosed — no prior therapy |
| `TEST-FL-001` | Follicular lymphoma | Treatment-naive |
| `TEST-FL-002` | Follicular lymphoma | Relapsed — ≥2 prior lines |
| `TEST-BC-001` | Breast cancer | TNBC |
| `TEST-BC-002` | Breast cancer | HER2-negative advanced |
| `TEST-CLL-001` | CLL | R/R — ≥1 prior line required |
| `TEST-CLL-002` | CLL | Treatment-naive |

All test trials use `recruitment_status=RECRUITING` and broad age limits (18–80+) to maximise match opportunities.

### Test patients in ctomop (7 total, person_ids 9001–9007)

| person_id | Disease | Age | Therapy lines | Designed to match |
|-----------|---------|-----|--------------|-------------------|
| 9001 | Multiple myeloma | 66 | 3 (R/R) | TEST-MM-001 |
| 9002 | Multiple myeloma | 54 | 0 (newly diagnosed) | TEST-MM-002 |
| 9003 | Follicular lymphoma | 59 | 0 (untreated) | TEST-FL-001 |
| 9004 | Follicular lymphoma | 69 | 2 (relapsed) | TEST-FL-002 |
| 9005 | Breast cancer (TNBC) | 49 | 1 | TEST-BC-001 |
| 9006 | CLL | 74 | 2 (R/R) | TEST-CLL-001 |
| 9007 | CLL | 64 | 0 (treatment-naive) | TEST-CLL-002 |

Person IDs 9001–9999 are reserved for test data and will not collide with patients loaded from real sources.

## Expected output

```
  person_id=9001 [multiple myeloma]         → 2 trials | 1 eligible | 1 potential | best: 88%
  person_id=9002 [multiple myeloma]         → 1 trials | 1 eligible | 0 potential | best: 92%
  person_id=9003 [follicular lymphoma]      → 1 trials | 1 eligible | 0 potential | best: 85%
  person_id=9004 [follicular lymphoma]      → 1 trials | 0 eligible | 1 potential | best: 71%
  person_id=9005 [breast cancer]            → 2 trials | 1 eligible | 1 potential | best: 83%
  person_id=9006 [chronic lymphocytic leukemia] → 1 trials | 1 eligible | 0 potential | best: 90%
  person_id=9007 [chronic lymphocytic leukemia] → 1 trials | 1 eligible | 0 potential | best: 87%

Done. Patients processed: 7, Errors: 0
```

Exact scores will vary. If a patient returns 0 trials, check:

1. `seed_reference_data` was run before `seed_test_trials`
2. The exact dev server is running and reachable
3. Disease strings match exactly (case-insensitive comparison is handled by the API)

## Cleaning up

```bash
# Remove test trials from exact
python manage.py seed_test_trials --clear

# Remove test patients from ctomop
DATABASE_URL=$PATIENT_DATABASE_URL python manage.py seed_test_patients --clear
```
