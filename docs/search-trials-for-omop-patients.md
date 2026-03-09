# search_trials_for_omop_patients

Management command that reads `PatientInfo` records from an exactomop (OMOP CDM) database and calls the exact Trials Search API for each patient, producing a ranked list of matching clinical trials.

## Usage

```bash
# Minimal — print per-patient summary to stdout
python manage.py search_trials_for_omop_patients \
  --source-db-url postgresql://user:pass@host:5432/exactomop \
  --api-url http://localhost:8000 \
  --api-token <your-token>

# Specific patients only
python manage.py search_trials_for_omop_patients \
  --source-db-url $EXACTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --person-ids 42,107,883

# Save full trial details to JSON
python manage.py search_trials_for_omop_patients \
  --source-db-url $EXACTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --output results.json

# Save compact summary to CSV
python manage.py search_trials_for_omop_patients \
  --source-db-url $EXACTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --output results.csv --format csv

# Preview request body for the first patient without calling the API
python manage.py search_trials_for_omop_patients \
  --source-db-url $EXACTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --dry-run

# Custom goodness score weights (benefit/patient-burden/risk/distance, default 25 each)
python manage.py search_trials_for_omop_patients \
  --source-db-url $EXACTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --benefit-weight 40 \
  --patient-burden-weight 20 \
  --risk-weight 20 \
  --distance-penalty-weight 20 \
  --output results.json
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--source-db-url` | `EXACTOMOP_DATABASE_URL` env var | PostgreSQL connection URL for the exactomop database |
| `--api-url` | `EXACT_API_URL` env var or `http://localhost:8000` | Base URL of the exact API |
| `--api-token` | `EXACT_API_TOKEN` env var | API authentication token |
| `--person-ids` | all | Comma-separated person IDs to process |
| `--batch-size` | 100 | Number of patients fetched per DB round-trip |
| `--limit` | 50 | Maximum trials returned per patient from the API |
| `--sort` | `matchScore` | Trial sort order: `matchScore`, `goodnessScore`, `distance`, `status`, `phase`, `updated`, `enrollment`, `patientBurdenScore` |
| `--benefit-weight` | `25.0` | Goodness score benefit component weight |
| `--patient-burden-weight` | `25.0` | Goodness score patient burden component weight |
| `--risk-weight` | `25.0` | Goodness score risk component weight |
| `--distance-penalty-weight` | `25.0` | Goodness score distance penalty component weight |
| `--output` | _(stdout only)_ | File path to write results (`--format` controls the format) |
| `--format` | `json` | Output format for `--output`: `json` or `csv` |
| `--dry-run` | off | Print the API request body for the first patient and exit without making search calls |

## Goodness score weights

The goodness score is a composite metric combining four components:

| Component | Flag | Default |
|-----------|------|---------|
| Benefit score | `--benefit-weight` | `25.0` |
| Patient burden score | `--patient-burden-weight` | `25.0` |
| Risk score | `--risk-weight` | `25.0` |
| Distance penalty | `--distance-penalty-weight` | `25.0` |

The weights do not need to sum to 100 — they are relative. A higher weight amplifies that component's influence on the final score.

Example — prioritise benefit, de-emphasise distance:

```bash
python manage.py search_trials_for_omop_patients \
  --source-db-url $EXACTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --sort goodnessScore \
  --benefit-weight 50 \
  --patient-burden-weight 20 \
  --risk-weight 20 \
  --distance-penalty-weight 10 \
  --output results.json
```

## How it works

1. Connects to exactomop via psycopg2 (raw SQL — exact does not have exactomop's Django models)
2. Reads `patient_info` rows in batches
3. Converts each row to the exact API request body:
   - snake_case field names → camelCase (e.g. `patient_age` → `patientAge`)
   - `NULL` values are omitted
   - exactomop-only columns are skipped (see [Skipped columns](#skipped-columns))
   - JSON fields (`later_therapies`, `supportive_therapies`, `genetic_mutations`, `stem_cell_transplant_history`) are decoded from strings if needed
   - `date` values are formatted as ISO strings
4. Calls `GET /trials/` with `{"patient_info": {...}}` in the request body and `Authorization: Token <token>` header
5. Prints a one-line summary per patient to stdout
6. Optionally writes full results to a file

## Stdout output

Each processed patient produces one summary line:

```
  person_id=42 ext=42 [chronic lymphocytic leukemia] → 18 total | 6 eligible | 12 potential | best score: 94%
  person_id=107 ext=107 [multiple myeloma] → 31 total | 11 eligible | 20 potential | best score: 88%
  person_id=883 ext=883 [breast cancer] → 9 total | 3 eligible | 6 potential | best score: 76%

Done. Patients processed: 3, Errors: 0
```

| Column | Description |
|--------|-------------|
| `total` | Total number of matching trials in the database |
| `eligible` | Trials where all required patient attributes are already filled (`matchingType=eligible`) |
| `potential` | Trials where some attributes are still needed (`matchingType=potential`) |
| `best score` | Highest `matchScore` (0–100 %) across the returned trials |

## JSON output (`--output results.json`)

An array of objects, one per patient:

```json
[
  {
    "person_id": 42,
    "external_id": "42",
    "disease": "chronic lymphocytic leukemia",
    "total_trials": 18,
    "returned_trials": 18,
    "eligible_count": 6,
    "potential_count": 12,
    "best_match_score": 94,
    "trials": [
      {
        "trialId": 1001,
        "studyId": "NCT04568888",
        "briefTitle": "Zanubrutinib vs Ibrutinib in R/R CLL",
        "phase": ["Phase 3"],
        "recruitingStatus": "RECRUITING",
        "matchScore": 94,
        "matchingType": "eligible",
        "attributesToFillIn": [],
        "goodnessScore": 87,
        "distance": 12,
        "distanceUnits": "miles",
        "interventionTreatments": ["Zanubrutinib", "Ibrutinib"],
        "sponsor": "BeiGene"
      }
    ]
  }
]
```

## CSV output (`--output results.csv --format csv`)

One row per patient with a compact summary:

```csv
person_id,external_id,disease,total_trials,eligible_count,potential_count,best_match_score,top_trial_ids
42,42,chronic lymphocytic leukemia,18,6,12,94,NCT04568888,NCT05112345,NCT04901234
107,107,multiple myeloma,31,11,20,88,NCT04775069,NCT04839536
883,883,breast cancer,9,3,6,76,NCT04961840
```

`top_trial_ids` contains the NCT IDs of the first 5 trials returned (already sorted by `--sort`).

## Dry run example

`--dry-run` prints the API request body that would be sent for the first patient, then exits:

```
person_id=42, disease=chronic lymphocytic leukemia
Request body:
{
  "patient_info": {
    "externalId": "42",
    "patientAge": 67,
    "gender": "M",
    "disease": "chronic lymphocytic leukemia",
    "country": "DE",
    "binetStage": "B",
    "absoluteLymphocyteCount": 38.4,
    "lymphocyteDoublingTime": 4,
    "serumBeta2MicroglobulinLevel": 5.2,
    "tp53Disruption": true,
    "btkInhibitorRefractory": false,
    "hemoglobinLevel": 10.8,
    "hemoglobinLevelUnits": "G/DL",
    "plateletCount": 112000,
    "priorTherapy": "Two lines",
    "firstLineTherapy": "FCR",
    "secondLineTherapy": "Ibrutinib",
    "laterTherapies": [],
    "noOtherActiveMalignancies": true,
    "noHivStatus": true,
    "noHepatitisBStatus": true,
    "noHepatitisCStatus": true
  }
}
```

## Skipped columns

The following exactomop-specific columns are excluded from the API body:

`person_id`, `id`, `condition_code_icd_10`, `condition_code_snomed_ct`, `therapy_lines_count`, `line_of_therapy`, `liver_enzyme_levels`, `serum_bilirubin_level`, `remission_duration_min`, `washout_period_duration`, `hiv_status`, `hepatitis_b_status`, `hepatitis_c_status`, `languages`, `language_skill_level`, `old_supportive_therapies`, `geo_point`

`languages` and `language_skill_level` are excluded because they are already merged into `languages_skills` on the exactomop side (see [exactomop-patient-info-diff.md](exactomop-patient-info-diff.md)).

## Getting an API token

The exact API uses token authentication. Obtain a token once with your Django username and password, then reuse it for all subsequent requests.

### curl

```bash
curl -s -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'
```

Response:

```json
{"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}
```

### Store and reuse in one step (bash)

```bash
export EXACT_API_TOKEN=$(
  curl -s -X POST http://localhost:8000/api-token-auth/ \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${EXACT_USER}\", \"password\": \"${EXACT_PASSWORD}\"}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])"
)

echo "Token: $EXACT_API_TOKEN"
```

### Full get-token script (`get_token.sh`)

```bash
#!/usr/bin/env bash
# Usage: source get_token.sh
#   or:  export EXACT_API_TOKEN=$(bash get_token.sh)

API_URL="${EXACT_API_URL:-http://localhost:8000}"
USERNAME="${EXACT_USER:?EXACT_USER is not set}"
PASSWORD="${EXACT_PASSWORD:?EXACT_PASSWORD is not set}"

EXACT_API_TOKEN=$(
  curl -sf -X POST "${API_URL}/api-token-auth/" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])"
)

if [ -z "$EXACT_API_TOKEN" ]; then
  echo "ERROR: failed to obtain token (wrong credentials or API unreachable?)" >&2
  exit 1
fi

export EXACT_API_TOKEN
echo "$EXACT_API_TOKEN"
```

Run the full workflow:

```bash
export EXACT_USER=admin
export EXACT_PASSWORD=secret
export EXACT_API_URL=http://localhost:8000
export EXACTOMOP_DATABASE_URL=postgresql://user:pass@host:5432/exactomop

# 1. Get token
source get_token.sh

# 2. Run the search
python manage.py search_trials_for_omop_patients \
  --source-db-url "$EXACTOMOP_DATABASE_URL" \
  --api-url "$EXACT_API_URL" \
  --api-token "$EXACT_API_TOKEN" \
  --output results.json
```

> **Token lifetime:** DRF tokens do not expire by default. The same token can be reused indefinitely. To revoke it, delete the token via the Django admin or `python manage.py drf_create_token --reset-token <username>`.

## Environment variables

```bash
export EXACTOMOP_DATABASE_URL=postgresql://user:pass@host:5432/exactomop
export EXACT_API_URL=https://exact.example.com
export EXACT_API_TOKEN=abc123...
```

All three can be passed as CLI flags instead (`--source-db-url`, `--api-url`, `--api-token`). CLI flags take precedence over environment variables.

## Relation to other commands

| Command | Purpose |
|---------|---------|
| `load_patient_info_from_omop` | ETL: copies PatientInfo from exactomop into exact's database |
| `search_trials_for_omop_patients` | Search: reads PatientInfo from exactomop and calls exact's API directly, without writing to exact's database |

Use `load_patient_info_from_omop` when you want to persist patient records in exact for ongoing use. Use `search_trials_for_omop_patients` when you want a one-off batch search against the live exactomop data without touching exact's database.
