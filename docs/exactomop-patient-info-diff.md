# PatientInfo Model Differences: exact vs exactomop

Comparison of `PatientInfo` models between the two repos to evaluate DB-level integration.

- **exact**: `trials/models.py` — standalone model, auto PK, no FK to user/person
- **exactomop**: `omop/models.py` — `person = OneToOneField(Person)`, coupled to OMOP CDM

## Schema Alignment Status

**Aligned** as of migration `0002_align_patient_info_with_exact`. All fields, types, and
defaults now match between the two projects, except for the remaining differences below.

Run `backfill_patient_info_fields` in exactomop after migrating to populate new fields
from existing data (`external_id`, `languages_skills`, `supportive_therapies` JSON conversion).

## Remaining Differences

### Database Engine

- **exact**: PostGIS (`django.contrib.gis.db.backends.postgis`) — required for `geo_point` PointField
- **exactomop**: plain PostgreSQL or SQLite — no GIS support

### exact-only field

- `geo_point` — PointField (PostGIS), geospatial matching. Computed by `normalize_patient_info` from lat/lon/country. Not added to exactomop (requires PostGIS).

### Field Name Difference

| exact | exactomop |
|-------|-----------|
| `languages_skills` (single TextField) | `languages` + `language_skill_level` (two fields) + `languages_skills` (combined) |

exactomop now has all three fields. The `languages_skills` field is backfilled by
`backfill_patient_info_fields` from the existing `languages` + `language_skill_level`.

### Extra Fields in exactomop (not in exact)

- `person` — OneToOneField to OMOP Person
- `condition_code_icd_10` — TextField, ICD-10 code
- `condition_code_snomed_ct` — TextField, SNOMED code
- `therapy_lines_count` — IntegerField, legacy
- `line_of_therapy` — TextField, legacy
- `liver_enzyme_levels` — IntegerField, legacy (exact uses separate AST/ALT/ALP fields)
- `serum_bilirubin_level` — DecimalField, legacy (exact uses total/direct split)
- `remission_duration_min` — TextField
- `washout_period_duration` — TextField
- `hiv_status` — BooleanField (duplicates `no_hiv_status`)
- `hepatitis_b_status` — BooleanField (duplicates `no_hepatitis_b_status`)
- `hepatitis_c_status` — BooleanField (duplicates `no_hepatitis_c_status`)

## Integration Options

1. **Align exactomop → exact schema** (done): Added missing fields to exactomop, fixed types. To complete: upgrade to PostGIS for `geo_point`, then point exact's `PATIENT_DB_URL` at the exactomop database via `PatientInfoRouter`.

2. **ETL layer** (done): `exact/trials/management/commands/load_patient_info_from_omop.py` reads from exactomop and creates/updates PatientInfo records in exact. See [load-patient-info-from-omop.md](load-patient-info-from-omop.md).
