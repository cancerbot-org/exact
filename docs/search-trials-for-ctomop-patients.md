# search_trials_for_ctomop_patients

Management command that reads `PatientInfo` records from a ctomop database and calls the exact Trials Search API for each patient, producing a ranked list of matching clinical trials.

Supports two source modes: **direct DB access** (recommended) and **ctomop REST API access** (for environments where only HTTP is available).

## Usage

### DB mode (default)

```bash
# Minimal — print per-patient summary to stdout
python manage.py search_trials_for_ctomop_patients \
  --source-db-url postgresql://user:pass@host:5432/ctomop \
  --api-url http://localhost:8000 \
  --api-token <your-token>

# Specific patients only
python manage.py search_trials_for_ctomop_patients \
  --source-db-url $CTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --person-ids 42,107,883

# Save full trial details to JSON
python manage.py search_trials_for_ctomop_patients \
  --source-db-url $CTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --output results.json

# Save compact summary to CSV
python manage.py search_trials_for_ctomop_patients \
  --source-db-url $CTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --output results.csv --format csv

# Preview request body for the first patient without calling the exact API
python manage.py search_trials_for_ctomop_patients \
  --source-db-url $CTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --dry-run

# Custom goodness score weights
python manage.py search_trials_for_ctomop_patients \
  --source-db-url $CTOMOP_DATABASE_URL \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --benefit-weight 40 \
  --patient-burden-weight 20 \
  --risk-weight 20 \
  --distance-penalty-weight 20 \
  --output results.json
```

### API mode

Use `--use-api` when direct PostgreSQL access is not available. The command authenticates with Basic auth against the ctomop REST API, lists all patients, then fetches full detail records one by one.

```bash
python manage.py search_trials_for_ctomop_patients \
  --use-api \
  --source-api-url http://ctomop.example.com \
  --source-api-username admin \
  --source-api-password secret \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN

# Filter to specific patients in API mode
python manage.py search_trials_for_ctomop_patients \
  --use-api \
  --source-api-url $CTOMOP_API_URL \
  --source-api-username $CTOMOP_API_USERNAME \
  --source-api-password $CTOMOP_API_PASSWORD \
  --person-ids 42,107 \
  --api-url $EXACT_API_URL \
  --api-token $EXACT_API_TOKEN \
  --output results.json
```

> **Note:** API mode issues one HTTP request per patient (N+1 pattern). For large patient populations, DB mode is significantly faster.

## Options

### Source — DB mode

| Option | Default | Description |
|--------|---------|-------------|
| `--source-db-url` | `CTOMOP_DATABASE_URL` env var | PostgreSQL connection URL for the ctomop database |

### Source — API mode

| Option | Default | Description |
|--------|---------|-------------|
| `--use-api` | off | Read patients from the ctomop REST API instead of direct DB |
| `--source-api-url` | `CTOMOP_API_URL` env var | Base URL of the ctomop API (e.g. `http://ctomop.example.com`) |
| `--source-api-username` | `CTOMOP_API_USERNAME` env var | ctomop API username (Basic auth) |
| `--source-api-password` | `CTOMOP_API_PASSWORD` env var | ctomop API password (Basic auth) |

### Exact API

| Option | Default | Description |
|--------|---------|-------------|
| `--api-url` | `EXACT_API_URL` env var or `http://localhost:8000` | Base URL of the exact API |
| `--api-token` | `EXACT_API_TOKEN` env var | exact API authentication token |

### Filtering & batching

| Option | Default | Description |
|--------|---------|-------------|
| `--person-ids` | all | Comma-separated person IDs to process |
| `--batch-size` | 100 | Rows per DB round-trip — DB mode only |

### Trial search

| Option | Default | Description |
|--------|---------|-------------|
| `--limit` | 50 | Maximum trials returned per patient from the exact API |
| `--sort` | `matchScore` | Trial sort order: `matchScore`, `goodnessScore`, `distance`, `status`, `phase`, `updated`, `enrollment`, `patientBurdenScore` |

### Goodness score weights

| Option | Default | Description |
|--------|---------|-------------|
| `--benefit-weight` | `25.0` | Goodness score benefit component weight |
| `--patient-burden-weight` | `25.0` | Goodness score patient burden component weight |
| `--risk-weight` | `25.0` | Goodness score risk component weight |
| `--distance-penalty-weight` | `25.0` | Goodness score distance penalty component weight |

### Output

| Option | Default | Description |
|--------|---------|-------------|
| `--output` | _(stdout only)_ | File path to write results |
| `--format` | `json` | Output format for `--output`: `json` or `csv` |
| `--dry-run` | off | Print the API request body for the first patient and exit |

### Study preferences / search filters

| Option | Default | Description |
|--------|---------|-------------|
| `--search-title` | _(none)_ | Filter trials by title keyword |
| `--recruitment-status` | _(none)_ | Filter by recruitment status (e.g. `RECRUITING`) |
| `--sponsor` | _(none)_ | Filter trials by sponsor name |
| `--register` | _(none)_ | Filter by trial register (e.g. `ClinicalTrials.gov`) |
| `--trial-type` | _(none)_ | Filter by trial type |
| `--study-type` | _(none)_ | Filter by study type |
| `--study-id` | _(none)_ | Filter by specific study ID (e.g. NCT number) |
| `--validated-only` | off | Return only manually validated trials |
| `--distance` | _(none)_ | Maximum distance from patient location to trial site |
| `--distance-units` | `km` | Distance units: `km` or `miles` |
| `--country` | _(none)_ | Filter trials to a specific country code (e.g. `US`, `DE`) |
| `--region` | _(none)_ | Filter trials to a specific region/state |
| `--postal-code` | _(none)_ | Filter trials near a postal code |
| `--last-update` | _(none)_ | Filter trials updated after this date (`YYYY-MM-DD`) |
| `--first-enrolment` | _(none)_ | Filter trials with first enrolment after this date (`YYYY-MM-DD`) |

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
python manage.py search_trials_for_ctomop_patients \
  --source-db-url $CTOMOP_DATABASE_URL \
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

### DB mode

1. Connects to ctomop's PostgreSQL database via psycopg2
2. Reads `patient_info` rows in batches (joined with `person` for person_id)
3. Converts each row to the exact API request body (see [Field mapping](#field-mapping))
4. Calls `GET /trials/` with `{"patient_info": {...}}` and `Authorization: Token <token>`
5. Prints a one-line summary per patient to stdout
6. Optionally writes full results to file

### API mode

1. Authenticates with Basic auth to the ctomop REST API
2. `GET /api/patient-info/` → retrieves the list of patients (with IDs)
3. For each patient: `GET /api/patient-info/{id}/` → retrieves full PatientInfo detail
4. Applies the same field mapping and exact API call as DB mode

## Field mapping

Each ctomop `patient_info` row is converted to the exact API body:

- Snake_case field names → camelCase (`patient_age` → `patientAge`)
- `NULL` / `None` values are omitted
- JSON fields (`later_therapies`, `supportive_therapies`, `genetic_mutations`, `stem_cell_transplant_history`) are decoded from strings if needed
- `date` values are formatted as ISO strings (`2024-01-15`)
- ctomop-specific legacy columns are skipped (see [Skipped columns](#skipped-columns))

## Stdout output

Each processed patient produces one summary line:

```
  person_id=42 [chronic lymphocytic leukemia] → 18 total | 6 eligible | 12 potential | best score: 94%
  person_id=107 [multiple myeloma] → 31 total | 11 eligible | 20 potential | best score: 88%
  person_id=883 [breast cancer] → 9 total | 3 eligible | 6 potential | best score: 76%

Done. Patients processed: 3, Errors: 0
```

| Column | Description |
|--------|-------------|
| `total` | Total number of matching trials in the database |
| `eligible` | Trials where all required patient attributes are met (`matchingType=eligible`) |
| `potential` | Trials where some attributes are still needed (`matchingType=potential`) |
| `best score` | Highest `matchScore` (0–100 %) across the returned trials |

## JSON output (`--output results.json`)

An array of objects, one per patient:

```json
[
  {
    "person_id": 42,
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
person_id,disease,total_trials,eligible_count,potential_count,best_match_score,top_trial_ids
42,chronic lymphocytic leukemia,18,6,12,94,NCT04568888,NCT05112345,NCT04901234
107,multiple myeloma,31,11,20,88,NCT04775069,NCT04839536
883,breast cancer,9,3,6,76,NCT04961840
```

`top_trial_ids` contains the NCT IDs of the first 5 trials returned (sorted by `--sort`).

## Skipped columns

The following ctomop-specific and internal columns are excluded from the exact API body:

| Column(s) | Reason |
|-----------|--------|
| `id`, `person_id`, `person` | Internal PKs/FKs |
| `created_at`, `updated_at` | Timestamps |
| `email`, `date_of_birth` | PII not used for trial matching |
| `bmi` | Computed by exact from `weight` + `height` |
| `condition_code_icd_10`, `condition_code_snomed_ct` | ctomop legacy fields |
| `therapy_lines_count`, `line_of_therapy` | ctomop legacy fields |
| `liver_enzyme_levels`, `serum_bilirubin_level` | Legacy duplicates (exact uses named variants) |
| `hiv_status`, `hepatitis_b_status`, `hepatitis_c_status` | Legacy booleans (exact uses `no_hiv_status` etc.) |
| `geo_point` | PostGIS geography — ctomop uses `latitude`/`longitude` floats instead |
| `patient_name`, `age`, `refractory_status` | Computed API-only fields from ctomop serializer |

## Environment variables

```bash
# DB mode
export CTOMOP_DATABASE_URL=postgresql://user:pass@host:5432/ctomop

# API mode
export CTOMOP_API_URL=https://ctomop.example.com
export CTOMOP_API_USERNAME=admin
export CTOMOP_API_PASSWORD=secret

# exact API (both modes)
export EXACT_API_URL=https://exact.example.com
export EXACT_API_TOKEN=abc123...
```

CLI flags always take precedence over environment variables.

## Getting an exact API token

```bash
curl -s -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'
# → {"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}

export EXACT_API_TOKEN=9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## Full workflow example

```bash
export CTOMOP_DATABASE_URL=postgresql://user:pass@host:5432/ctomop
export EXACT_API_URL=https://exact.example.com
export EXACT_USER=admin
export EXACT_PASSWORD=secret

# 1. Get exact API token
export EXACT_API_TOKEN=$(
  curl -s -X POST "${EXACT_API_URL}/api-token-auth/" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${EXACT_USER}\", \"password\": \"${EXACT_PASSWORD}\"}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])"
)

# 2. Run the search (DB mode)
python manage.py search_trials_for_ctomop_patients \
  --source-db-url "$CTOMOP_DATABASE_URL" \
  --api-url "$EXACT_API_URL" \
  --api-token "$EXACT_API_TOKEN" \
  --output results.json
```

## Relation to other commands

| Command | Source | Purpose |
|---------|--------|---------|
| `search_trials_for_omop_patients` | exactomop DB | Batch trial search against exactomop patient data |
| `search_trials_for_ctomop_patients` | ctomop DB or API | Batch trial search against ctomop patient data |

Both commands read patient data on-the-fly and call exact's API without writing anything to exact's database.
