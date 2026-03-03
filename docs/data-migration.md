# Data Migration

This document covers how to move trial data from the upstream CancerBot project
into EXACT, and how to keep the two in sync.

---

## Overview

EXACT owns the trial catalog but gets its data from the main CancerBot database.
The migration has two parts:

1. **Reference / static data** — diseases, therapies, markers, trial types, etc.
   These are seeded from code using the `seed_reference_data` management command,
   not from a DB dump.

2. **Trial catalog data** — `Trial`, `Location`, `LocationTrial`, and related
   records. These are exported from CancerBot and imported into EXACT using
   Django's `dumpdata` / `loaddata` fixtures.

---

## Step-by-step migration

### Step 1 — Seed reference data in EXACT

Run this first, in the **EXACT** project. It creates all static lookup records
(diseases, therapy taxonomy, markers, trial types, pre-existing condition
categories, etc.) that the trial fixture depends on:

```bash
python manage.py seed_reference_data
```

This is idempotent — safe to re-run.

### Step 2 — Dump trial data from CancerBot

Run this in the **CancerBot** (source) project. The script exports four fixture
files into a timestamped directory:

```bash
cd /path/to/cancerbot
bash exact/scripts/dump_prod_data.sh
```

This produces:

```
dump_YYYYMMDD/
├── reference.json      # Therapy/marker/disease/trial-type records + connections
├── locations.json      # Location records (cities, geo_points)
├── trials.json         # Trial records with all criteria fields
└── location_trials.json # Trial ↔ Location links
```

### Step 3 — Copy the dump to EXACT

```bash
scp -r user@cancerbot-host:/path/to/cancerbot/dump_YYYYMMDD /path/to/exact/
```

Or just copy the directory locally if both projects are on the same machine.

### Step 4 — Load into EXACT

Run this in the **EXACT** project:

```bash
bash scripts/load_prod_data.sh dump_YYYYMMDD/
```

The script loads fixtures in dependency order:

```
1. seed_reference_data   (diseases, therapies, markers, trial types)
2. reference.json        (same records + cross-references from CancerBot)
3. locations.json        (Location objects with geo_points)
4. trials.json           (Trial records)
5. location_trials.json  (LocationTrial join records)
```

### Step 5 — Verify

```bash
python manage.py shell -c "from trials.models import Trial; print(Trial.objects.count(), 'trials loaded')"
```

---

## What gets migrated vs. what doesn't

| Data | Migrated? | How |
|---|---|---|
| Trials | Yes | `trials.json` fixture |
| Locations / sites | Yes | `locations.json` fixture |
| Trial–location links | Yes | `location_trials.json` fixture |
| Therapy taxonomy | Yes | `reference.json` + `seed_reference_data` |
| Marker taxonomy | Yes | `reference.json` + `seed_reference_data` |
| Trial types | Yes | `reference.json` + `seed_reference_data` |
| Patient profiles (`PatientInfo`) | **No** | Patient data is not migrated — EXACT builds new profiles via its own API |
| Chat history | **No** | Chat data stays in CancerBot |
| User accounts | **No** | EXACT uses token auth; create tokens separately |

---

## Keeping data in sync

EXACT's trial catalog is a downstream copy. There is currently no live replication
or webhook; sync is manual:

1. Re-run `dump_prod_data.sh` in CancerBot whenever new trials are extracted or
   updated.
2. In EXACT, run `loaddata` for the updated fixtures. Django `loaddata` uses
   `update_or_create` semantics for natural keys — existing records are updated,
   new ones are inserted, deleted trials are **not** removed automatically.

To remove trials that no longer exist in CancerBot, use `flush` + full reload,
or write a management command that deletes trials whose `study_id` is not in the
new fixture set.

---

## What `dump_prod_data.sh` exports

The dump script exports specific models in a defined order:

```bash
# reference.json (in CancerBot source)
trials.Country
trials.State
trials.Disease
trials.TherapyComponent
trials.Therapy
trials.TherapyRound
trials.MarkerCategory
trials.Marker
trials.TrialType
trials.TrialTypeDiseaseConnection
trials.DiseaseRoundTherapyConnection

# locations.json
trials.Location

# trials.json
trials.Trial

# location_trials.json
trials.LocationTrial
```

---

## What `load_prod_data.sh` does

```bash
Step 1: python manage.py seed_reference_data
Step 2: python manage.py loaddata $DIR/reference.json
Step 3: python manage.py loaddata $DIR/locations.json
Step 4: python manage.py loaddata $DIR/trials.json
Step 5: python manage.py loaddata $DIR/location_trials.json
```

Steps 2–5 use Django's `loaddata`, which calls `save()` on each object. For
`Trial` objects this triggers the model's `get_match_score` pre-computation.

---

## Model differences between CancerBot and EXACT

The `Trial` and `Location` models in EXACT are a subset of CancerBot's models.
Fields removed in EXACT (e.g. admin-only fields, user-assignment fields) are
silently ignored during `loaddata` because Django's serializer skips unknown
fields.

If CancerBot adds new trial-criteria fields that EXACT doesn't have yet, the
fixture will load successfully but those fields won't be matched against patient
data until EXACT adds them.

---

## First-time production setup checklist

- [ ] PostgreSQL database created with PostGIS extension
- [ ] `python manage.py migrate` run
- [ ] `python manage.py seed_reference_data` run
- [ ] CancerBot dump transferred and loaded via `load_prod_data.sh`
- [ ] At least one auth token created (`python manage.py drf_create_token <username>`)
- [ ] Trial count verified in Django shell or admin
- [ ] `/swagger/` reachable and returning 200
