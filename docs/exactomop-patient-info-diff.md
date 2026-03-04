# PatientInfo Model Differences: exact vs exactomop

Comparison of `PatientInfo` models between the two repos to evaluate DB-level integration.

- **exact**: `trials/models.py` — standalone model, auto PK, no FK to user/person
- **exactomop**: `omop/models.py` — `person = OneToOneField(Person)`, coupled to OMOP CDM

## Database Engine Difference

- **exact**: PostGIS (`django.contrib.gis.db.backends.postgis`) — required for `geo_point` PointField
- **exactomop**: plain PostgreSQL or SQLite — no GIS support

## Missing from exactomop

### CLL-specific fields (entire block — 22 fields)

- `binet_stage`
- `protein_expressions`
- `richter_transformation`
- `tumor_burden`
- `lymphocyte_doubling_time`
- `tp53_disruption`
- `measurable_disease_iwcll`
- `hepatomegaly`
- `autoimmune_cytopenias_refractory_to_steroids`
- `lymphadenopathy`
- `largest_lymph_node_size`
- `splenomegaly`
- `spleen_size`
- `disease_activity`
- `btk_inhibitor_refractory`
- `bcl2_inhibitor_refractory`
- `absolute_lymphocyte_count`
- `qtcf_value`
- `serum_beta2_microglobulin_level`
- `clonal_bone_marrow_b_lymphocytes`
- `clonal_b_lymphocyte_count`
- `bone_marrow_involvement`

### Other missing fields

- `external_id` — CharField(255), external system link
- `status` — TextField, patient status
- `geo_point` — PointField (PostGIS), geospatial matching
- `measurable_disease_imwg` — BooleanField, myeloma measurable disease
- `old_supportive_therapies` — TextField, legacy field
- `later_therapies` — JSONField(default=list), multiple later therapy lines

## Field Type Mismatches

| Field | exact | exactomop |
|-------|-------|-----------|
| `supportive_therapies` | `JSONField(default=list)` | `TextField` |
| `later_therapies` | `JSONField(default=list)` | **missing** (only `later_therapy` TextField) |
| `bone_only_metastasis_status` | `BooleanField(default=False)` non-nullable | `BooleanField` nullable |
| `metastatic_status` | `BooleanField(default=False)` non-nullable | `BooleanField` nullable |
| `measurable_disease_by_recist_status` | `BooleanField(default=False)` non-nullable | `BooleanField` nullable |
| `renal_adequacy_status` | `BooleanField(default=False)` non-nullable | `BooleanField` nullable |
| `plasma_cell_leukemia` | default=**False** | default=**True** (wrong default) |

## Field Name Differences

| exact | exactomop |
|-------|-----------|
| `languages_skills` (single TextField) | `languages` + `language_skill_level` (two fields) |

## Extra Fields in exactomop (not in exact)

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

1. **Align exactomop → exact schema**: Add missing fields to exactomop, fix types, upgrade to PostGIS. Then point exact's `PATIENT_DB_URL` at the exactomop database. exact already has `PatientInfoRouter` for this.

2. **Sync/ETL layer**: Keep schemas as-is. Build a service that transforms exactomop records into exact format (copy + map fields). Simpler but not real-time.

3. **DB view / foreign data wrapper**: Use PostgreSQL FDW to expose exactomop patient data to exact's database. Flexible but complex setup.
