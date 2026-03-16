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
PERSON_IDS=1,2,3 bash scripts/trials4patients.sh
```

## Run manually

```bash
cd /path/to/exact

python manage.py search_trials_for_patients \
  --source-db-url "$PATIENT_DATABASE_URL" \
  --person-ids "9001,9002,9003" \
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
```

This creates 8 test trials (2 per disease) in the local database:

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

To wipe and re-seed:

```bash
python manage.py seed_test_trials --clear
```

## Expected output

```
  person_id=9001 [multiple myeloma]         → 2 trials | 1 eligible | 1 potential | best: 88%
  person_id=9002 [multiple myeloma]         → 1 trials | 1 eligible | 0 potential | best: 92%
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
