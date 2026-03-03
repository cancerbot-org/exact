# EXACT — Architecture Overview

EXACT (EXtracting Attributes from Clinical Trials) is a standalone Django service
extracted from the CancerBot platform. It owns the trial catalog, patient profile
management, and the eligibility-matching engine.

---

## What it does

1. **Stores the trial catalog** — every `Trial` record and its 150+ structured
   eligibility-criteria fields.
2. **Stores patient profiles** (`PatientInfo`) — demographics, disease history,
   lab values, therapy lines, biomarkers, and geolocation.
3. **Matches patients to trials** — scores and ranks trials against a patient's
   profile using a disease-aware attribute matching algorithm.
4. **Exposes a REST API** — callers can pass a saved `patient_info_id` *or* send
   a one-off `patient_info` JSON object; no session state is required.

---

## High-level components

```
┌──────────────────────────────────────────────────────┐
│                   REST API (DRF)                     │
│  /patient-info/   /trials/   /trials-graph/          │
│  /form-settings/  /countries/  /locations/           │
└────────────────────┬─────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   resolve_patient_info  │  stateful (DB id) or
        │   (trials/services/     │  stateless (JSON body)
        │    patient_info/        │
        │    resolve.py)          │
        └────────────┬────────────┘
                     │
     ┌───────────────▼──────────────────┐
     │        TrialQuerySet             │
     │  filtered_trials()               │  SQL-level filters
     │  with_goodness_score_optimized() │  ORM annotations
     │  with_distance_optimized()       │
     └───────────────┬──────────────────┘
                     │
     ┌───────────────▼──────────────────┐
     │   UserToTrialAttrMatcher         │
     │   per-trial scoring & status     │  Python-level scoring
     │   (eligible / potential /        │
     │    not_eligible)                 │
     └───────────────┬──────────────────┘
                     │
     ┌───────────────▼──────────────────┐
     │  TrialTemplates / TrialAttributes│  Presentation layer
     │  attribute labeling & grouping   │
     └──────────────────────────────────┘
```

---

## Key models

| Model | Purpose |
|---|---|
| `Trial` | One clinical trial, ~150 eligibility-criteria fields |
| `PatientInfo` | Patient medical profile, ~100 fields |
| `Location` / `LocationTrial` | Geographic trial sites (PostGIS) |
| `StudyInfo` | Saved search preferences per patient |
| `Therapy` / `TherapyComponent` / `TherapyComponentCategory` | Therapy taxonomy |
| `Marker` / `MarkerCategory` | Biomarker taxonomy |
| `ConcomitantMedication` | Medication taxonomy |
| `PreExistingConditionCategory` | Comorbidity categories |
| `TrialType` / `TrialTypeDiseaseConnection` | Trial-type taxonomy by disease |
| `RawDataItem` | Raw ingested trial data before extraction |

---

## Key services

### `resolve_patient_info` (`trials/services/patient_info/resolve.py`)

The entry point for all API calls that need patient context. Supports two modes:

- **Stateful** — `?patient_info_id=<pk>`: loads a saved `PatientInfo` from the DB.
- **Stateless** — `"patient_info": {...}` in the request body: builds an unsaved
  in-memory `PatientInfo`, runs normalization, and returns it without writing to
  the DB. The caller's data is never persisted.

### `normalize_patient_info` (`trials/services/patient_info/normalize.py`)

Pure function (no DB write). Computes all derived fields from raw inputs:

- Clears downstream therapy fields when `prior_therapy` is reduced
- Computes treatment refractory status from therapy outcomes
- Sets `geo_point` from country/postal code or lat/lon
- Computes FLIPI score (follicular lymphoma)
- Derives TNBC and HR status from receptor statuses (breast cancer)
- Derives metastatic status and IMWG measurable-disease criteria (myeloma)
- Sets `last_treatment` date from the most recent therapy line

Called explicitly on create/update in the API views, and automatically via a
`pre_save` signal on subsequent saves of existing records.

### `UserToTrialAttrMatcher` (`trials/services/user_to_trial_attr_matcher.py`)

Per-trial scoring engine. Given one `(trial, patient_info)` pair:

- Returns a **match status**: `eligible`, `potential`, or `not_eligible`
- Returns a **match score** (0–100): percentage of checked attributes that match
- Returns per-attribute statuses: `matched`, `unknown`, or `not_matched`
- Is disease-aware — skips attributes that don't apply to the patient's disease

### `TrialQuerySet` (`trials/querysets/trial.py`)

The SQL-level filtering layer. Key methods:

- `filtered_trials(search_options, study_info, patient_info)` — applies all
  active filters (disease, therapy, markers, distance, etc.) and annotates the
  queryset with `match_score`.
- `with_goodness_score_optimized()` — annotates with a weighted composite score
  (benefit, patient burden, risk, distance).
- `with_distance_optimized(geo_point)` — annotates with distance to nearest
  recruiting site.
- `with_potential_attrs_count(patient_info)` — annotates each trial with the
  count of patient attributes that are blank but required.

### `TrialTemplates` / `TrialAttributes` (`trials/services/trial_details/`)

Presentation layer. Formats trial details for API responses:

- Groups attributes into display buckets (`general`, `trialEligibilityAttributes`)
- Attaches patient values alongside trial values for each attribute
- Computes per-attribute matching types for display

### `ValueOptions` (`trials/services/value_options.py`)

Single source of truth for all enumeration dropdowns (therapies by disease,
markers, outcomes, staging options, ethnicity, etc.). Consumed by the API's
`/form-settings/` endpoint and by `TrialAttributes`.

---

## Patient-info normalization lifecycle

```
POST /patient-info/          PATCH /patient-info/{id}/      GET /trials/?patient_info_id=
        │                            │                               │
   API view creates             API view loads                  resolve() loads
   PatientInfo                  PatientInfo                     PatientInfo from DB
        │                            │
   normalize_patient_info()    normalize_patient_info()
   (explicit call)             (explicit call)
        │                            │
   patient_info.save()         patient_info.save()
        │                            │
   pre_save signal ─────────── pre_save signal
   (skipped on first           (runs normalize again
    create: no pk yet)          as a safety net)
```

For **stateless** requests (JSON body), `resolve_patient_info` builds an
in-memory instance, runs `normalize_patient_info`, and returns it — nothing is
written to the DB.

---

## Database

PostgreSQL 16 with PostGIS. Key indexes:

- `GistIndex` on `PatientInfo.geo_point` and `Location.geo_point` for fast
  distance queries.
- `GinIndex` on trial JSON array fields (therapies, markers, stages) for
  containment lookups.

### Optional split-database configuration

`PatientInfo` can be routed to a separate PostgreSQL database (e.g. for privacy
isolation) by setting `PATIENT_DB_URL`. The `PatientInfoRouter` in
`exact/routers.py` handles read/write routing automatically. When unset,
everything uses the default DB.

---

## Authentication

All API endpoints require authentication. The service supports:

- **Token authentication** (`Authorization: Token <token>`) — primary method
  for service-to-service calls.
- **Session authentication** — for browser-based clients / Django admin.

Tokens are managed via the standard DRF `rest_framework.authtoken` app.

---

## Diseases supported

| Code | Disease |
|------|---------|
| MM | Multiple Myeloma |
| FL | Follicular Lymphoma |
| BC | Breast Cancer |
| CLL | Chronic Lymphocytic Leukemia |

The matching engine is disease-aware: criteria that don't apply to a patient's
disease are skipped entirely rather than marked as "not matched".
