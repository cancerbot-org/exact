# scripts/

## `trials4patients.sh`

End-to-end patient–trial matching against live databases. No web server required — runs entirely via the Django ORM in-process.

### Prerequisites

- EXACT local DB migrated (`python manage.py migrate`)
- `TRIALS_DATABASE_URL` — PostgreSQL connection string for the trials database
- `PATIENT_DATABASE_URL` — PostgreSQL connection string for the patient database

### Usage

Run from the `exact/` project root:

```bash
export TRIALS_DATABASE_URL=postgresql://user:pass@host:5432/trials
export PATIENT_DATABASE_URL=postgresql://user:pass@host:5432/patients

bash scripts/trials4patients.sh
```

Or put both variables in a `.env` file at the project root — the script loads it automatically.

The script runs three steps:

| Step | What happens |
|------|-------------|
| 1 | Verifies connectivity and counts available trials |
| 2 | Runs `search_trials_for_patients` for all patients (top 20 trials each) |
| 3 | Prints a per-patient summary; full JSON saved to `/tmp/exact_local_test_results.json` |

### Options

```bash
# Run for specific patients only
PERSON_IDS=1,2,3 bash scripts/trials4patients.sh

# Limit to the first N patients (ordered by person_id)
PATIENT_LIMIT=50 bash scripts/trials4patients.sh
```

### Output

Summary printed to stdout:

```
  person_id=9001 [breast cancer] → 42 trials | 18 eligible | 24 potential | best match: 100% | best goodness: 87.5
  person_id=9002 [multiple myeloma] → 31 trials | 9 eligible | 22 potential | best match: 95% | best goodness: 74.0
```

Full per-patient results (trial IDs, scores, match types) written to `/tmp/exact_local_test_results.json`.

