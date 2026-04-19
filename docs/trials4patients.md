# trials4patients.sh

Runs EXACT trial matching for a set of patients directly against the patient
and trial databases — no web server required. Results are written to a JSON
file and optionally to an evaluator-compatible CSV.

---

## Prerequisites

1. EXACT local DB migrated: `python manage.py migrate`
2. `TRIALS_DATABASE_URL` — remote trials database
3. `PATIENT_DATABASE_URL` — patient database

---

## Usage

```bash
bash scripts/trials4patients.sh
```

All configuration is via environment variables. The script loads `.env` from
the project root automatically, so the recommended approach is to copy
`scripts/.env.example` to `.env`, fill in the values, and just run:

```bash
bash scripts/trials4patients.sh
```

---

## Environment variables

| Var | Default | Description |
|---|---|---|
| `TRIALS_DATABASE_URL` | required | Remote trials PostgreSQL database |
| `PATIENT_DATABASE_URL` | required | Patient PostgreSQL database |
| `PERSON_IDS` | all | Comma-separated person IDs to process |
| `PATIENT_LIMIT` | all | Max number of patients to process |
| `SEARCH_LIMIT` | `20` | Top N trials returned per patient |
| `RESULTS_CSV` | — | If set, also writes results in evaluator CSV format to this path |

---

## Output

Always writes a full JSON results file to `/tmp/exact_local_test_results.json`.

If `RESULTS_CSV` is set, also writes an evaluator-compatible CSV:

```
CTOMOP Patient ID,Trial,Eligible/Potential,Suitability Score
20291,NCT03452774,potential,81
20291,NCT07038785,eligible,79
```

This CSV can be passed directly to the evaluator — see [evaluator.md](evaluator.md).

---

## Examples

Typical `.env` for running against specific patients and saving evaluator CSV:

```bash
TRIALS_DATABASE_URL=postgresql://user:pass@host:5432/trials
PATIENT_DATABASE_URL=postgresql://user:pass@host:5432/patients

PERSON_IDS=20291,20292,20293
SEARCH_LIMIT=5
RESULTS_CSV=results.csv
```

Then just:

```bash
bash scripts/trials4patients.sh
```

To set `PERSON_IDS` from an ethalon CSV before running:

```bash
PERSON_IDS=$(tail -n +2 scripts/evaluator/ethalon.csv | cut -d',' -f1 | sort -u | tr '\n' ',' | sed 's/,$//') \
bash scripts/trials4patients.sh
```
