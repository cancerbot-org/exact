# load_patient_info_from_omop

Management command to ETL patient data from an exactomop (OMOP CDM) database into exact's `PatientInfo` model.

## Usage

```bash
python manage.py load_patient_info_from_omop \
  --source-db-url postgresql://user:pass@host:5432/exactomop

# Load specific patients
python manage.py load_patient_info_from_omop \
  --source-db-url postgresql://user:pass@host:5432/exactomop \
  --person-ids 1,2,3

# Preview without writing
python manage.py load_patient_info_from_omop \
  --source-db-url postgresql://user:pass@host:5432/exactomop \
  --dry-run
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--source-db-url` | `EXACTOMOP_DATABASE_URL` env var | PostgreSQL connection URL for the exactomop database |
| `--person-ids` | all | Comma-separated person IDs to load |
| `--batch-size` | 100 | Number of rows to fetch per batch |
| `--dry-run` | off | Log mapped fields per patient without writing to the database |

## How it works

1. Connects to the exactomop database via psycopg2 (raw SQL — exact does not have exactomop's Django models)
2. Queries `patient_info` joined with `person` (for `year_of_birth` fallback)
3. Maps each row to exact's `PatientInfo` fields (see field mapping below)
4. Creates or updates records using `external_id = str(person_id)` as the linking key
5. On create, calls `normalize_patient_info()` explicitly (the pre_save signal skips new instances). On update, the signal handles normalization automatically.
6. Derived fields (BMI, geo_point, FLIPI score, TNBC status, etc.) are computed by `normalize_patient_info()` and the model's `save()` method — they are not copied from the source.

## Field mapping

### Special mappings

| Source (exactomop) | Target (exact) | Transformation |
|---|---|---|
| `person_id` | `external_id` | Cast to `str`, used as linking key |
| `languages` + `language_skill_level` | `languages_skills` | Joined with ` - ` separator |
| `supportive_therapies` (TextField) | `supportive_therapies` (JSONField) | JSON-parsed if possible, otherwise wrapped in a list |
| `year_of_birth` (from person table) | `patient_age` | `current_year - year_of_birth`, only when `patient_age` is null |
| `plasma_cell_leukemia` | `plasma_cell_leukemia` | `None` coalesced to `False` (exactomop has wrong default) |

### Nullable → non-nullable boolean coalescing

Fields that are nullable in exactomop but non-nullable in exact are coalesced to their model defaults when the source value is `None`:

- **Default `True`**: `no_other_active_malignancies`, `consent_capability`, `no_pregnancy_or_lactation_status`, `no_mental_health_disorder_status`, `no_concomitant_medication_status`, `no_tobacco_use_status`, `no_substance_use_status`, `no_geographic_exposure_risk`, `no_hiv_status`, `no_hepatitis_b_status`, `no_hepatitis_c_status`, `no_active_infection_status`
- **Default `False`**: `pulmonary_function_test_result`, `bone_imaging_result`, `caregiver_availability_status`, `contraceptive_use`, `pregnancy_test_result`, `bone_only_metastasis_status`, `measurable_disease_by_recist_status`

### Fields defaulting to empty (not in exactomop)

| Field | Default |
|---|---|
| `later_therapies` | `[]` — now populated by exactomop's `migrate_omop_to_patientinfo` (lines 3+) |
| 22 CLL-specific fields | `None` — now populated by exactomop's `migrate_omop_to_patientinfo` for CLL patients |
| `geo_point` | Computed by `normalize_patient_info` from country/postal_code or lat/lon |
| `measurable_disease_imwg` | Computed by `normalize_patient_info` |

> **Note:** Since the exactomop schema was aligned with exact (migration `0002`), all 22 CLL fields,
> `later_therapies`, `external_id`, `languages_skills`, and `measurable_disease_imwg` are now
> present in the `patient_info` table on the exactomop side and will be copied directly by name.
> The "defaulting to empty" behaviour above applies only when reading from an older exactomop
> instance that has not yet been migrated.

### Ignored source columns

These exactomop-only columns are skipped during mapping:

`condition_code_icd_10`, `condition_code_snomed_ct`, `therapy_lines_count`, `line_of_therapy`, `liver_enzyme_levels`, `serum_bilirubin_level`, `remission_duration_min`, `washout_period_duration`, `hiv_status`, `hepatitis_b_status`, `hepatitis_c_status`

### All other shared fields (~80)

Copied directly by name. See [exactomop-patient-info-diff.md](exactomop-patient-info-diff.md) for the full schema comparison.
