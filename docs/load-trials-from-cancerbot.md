# load_trials_from_cancerbot

Management command that reads trial catalog data from a CancerBot PostgreSQL database and upserts it into this EXACT database.

Copies five tables in dependency order: `Country → State → Location → Trial → LocationTrial`, using natural-key upserts and automatic FK remapping.

## Quick start

```bash
# 1. Make sure EXACT's schema is ready
python manage.py migrate

# 2. Run the full pull (seeds reference data + loads trials)
bash scripts/pull_from_cancerbot.sh "postgresql://user:pass@host:5432/cancerbot"
```

Or run the management command directly:

```bash
python manage.py load_trials_from_cancerbot \
  --source-db-url postgresql://user:pass@host:5432/cancerbot
```

Falls back to the `CANCERBOT_DATABASE_URL` environment variable if `--source-db-url` is not provided.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--source-db-url` | `CANCERBOT_DATABASE_URL` env var | PostgreSQL connection URL for the CancerBot database |
| `--dry-run` | off | Read and count source rows without writing to EXACT |
| `--skip-locations` | off | Skip Country / State / Location; load Trials and LocationTrials only |
| `--batch-size` | 200 | Rows fetched per DB round-trip |

## Full workflow (`pull_from_cancerbot.sh`)

The shell script wraps the full migration in the correct order:

```bash
export CANCERBOT_DATABASE_URL=postgresql://user:pass@host:5432/cancerbot

bash scripts/pull_from_cancerbot.sh
```

Steps performed:

1. `python manage.py seed_reference_data` — creates diseases, therapy taxonomy, markers, trial types
2. `python manage.py load_trials_from_cancerbot` — copies Countries, States, Locations, Trials, LocationTrials
3. Prints a verification count (Countries / Locations / Trials / Links)

## How it works

### 1. Countries

Upserted by `title`. Mapping of source PK → EXACT PK is built in memory for FK remapping in subsequent steps.

### 2. States

Upserted by `(title, country)`. Country FK resolved via the country map built in step 1.

### 3. Locations

Upserted by `title`. The `geo_point` PostGIS column is reconstructed from `ST_X` / `ST_Y` into an EXACT `Point(lon, lat, srid=4326)` object. State and Country FKs resolved via the maps from steps 1–2.

### 4. Trials

The command introspects both source and target schemas at runtime:

- Fetches column names from `information_schema.columns` for `trials_trial` in the source DB
- Fetches field names from EXACT's `Trial._meta`
- Copies only the **intersection** — extra columns in either direction are silently ignored

This makes the command safe against schema drift: if CancerBot has columns that EXACT doesn't (or vice versa), the load still succeeds.

`trial_type` FK is resolved by matching `code` against locally seeded `TrialType` records (created by `seed_reference_data`). Upserted by `code`.

### 5. LocationTrials

Upserted by `(trial, location)`. Both FKs resolved via the trial and location maps built in steps 3–4.

## Idempotency

All upserts use `update_or_create` with natural keys. The command is safe to re-run at any time — existing records are updated, new ones are inserted, nothing is deleted.

To remove trials that no longer exist in CancerBot, delete them manually or truncate and reload:

```bash
python manage.py shell -c "
from trials.models import Trial
Trial.objects.all().delete()
"
python manage.py load_trials_from_cancerbot --source-db-url $CANCERBOT_DATABASE_URL
```

## Dry run

Preview what would be loaded without writing anything:

```bash
python manage.py load_trials_from_cancerbot \
  --source-db-url $CANCERBOT_DATABASE_URL \
  --dry-run
```

Output example:

```
--- Countries ---
  [dry] country: United States
  [dry] country: Germany
  ...
--- States ---
  [dry] state: California
  ...
--- Locations ---
  [dry] 1 842 locations would be upserted
--- Trials ---
  Copying 148 common columns (of 152 in EXACT)
  [dry] 3 201 trials would be upserted
--- LocationTrials ---
  [dry] ~12 440 location-trial links would be upserted, 0 skipped
```

## Refreshing trials only

If locations are already loaded and you only need to refresh trial records:

```bash
python manage.py load_trials_from_cancerbot \
  --source-db-url $CANCERBOT_DATABASE_URL \
  --skip-locations
```

## Environment variables

```bash
export CANCERBOT_DATABASE_URL=postgresql://user:pass@host:5432/cancerbot
```

## Verification

```bash
python manage.py shell -c "
from trials.models import Trial, Location, LocationTrial, Country
print('Countries :', Country.objects.count())
print('Locations :', Location.objects.count())
print('Trials    :', Trial.objects.count())
print('Links     :', LocationTrial.objects.count())
"
```

## Relation to other commands

| Command | Purpose |
|---------|---------|
| `seed_reference_data` | Creates static lookup records (diseases, therapies, markers, trial types) — run this first |
| `load_trials_from_cancerbot` | ETL: copies trial catalog from CancerBot into EXACT |
| `search_trials_for_omop_patients` | Batch trial search using exactomop patient data |
| `search_trials_for_ctomop_patients` | Batch trial search using ctomop patient data |
