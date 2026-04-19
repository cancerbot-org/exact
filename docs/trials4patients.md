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

All configuration is via environment variables. Set them inline or export
beforehand, or put them in a `.env` file at the project root.

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

Run for all patients, top 20 trials each:

```bash
PATIENT_DATABASE_URL=postgresql://... \
TRIALS_DATABASE_URL=postgresql://... \
bash scripts/trials4patients.sh
```

Run for specific patients with limit 5, save evaluator CSV:

```bash
PATIENT_DATABASE_URL=postgresql://... \
TRIALS_DATABASE_URL=postgresql://... \
PERSON_IDS=20291,20292,20293 \
SEARCH_LIMIT=5 \
RESULTS_CSV=results.csv \
bash scripts/trials4patients.sh
```

Extract person IDs from an ethalon CSV and run:

```bash
PERSON_IDS=$(tail -n +2 scripts/evaluator/ethalon.csv | cut -d',' -f1 | sort -u | tr '\n' ',' | sed 's/,$//') \
SEARCH_LIMIT=5 \
RESULTS_CSV=results.csv \
bash scripts/trials4patients.sh
```
