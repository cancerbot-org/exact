# API Reference

Base path: `/` (no versioning prefix).

Interactive docs are available at runtime:
- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`

All endpoints require an `Authorization: Token <token>` header unless noted
otherwise.

JSON payloads and responses use **camelCase** keys (converted by
`djangorestframework-camel-case`).

---

## Patient info

### Resolve patient context

Every trial-search endpoint needs a patient profile. There are two ways to
provide it — you can use either for any request:

| Mode | How |
|------|-----|
| **Stateful** | Add `?patient_info_id=<id>` to the query string |
| **Stateless** | Include `"patientInfo": {...}` in the request body |

The stateless mode never writes to the database. It builds an in-memory
`PatientInfo` from the JSON, runs normalization (computes BMI, geo_point, derived
statuses, etc.), and discards it at the end of the request.

---

### `POST /patient-info/`

Create a new patient profile. Returns the created object with all computed fields.

**Request body** (all fields optional unless noted):

```json
{
  "externalId": "string",
  "patientAge": 55,
  "gender": "M | F | UN",
  "weight": 75,
  "weightUnits": "kg | lbs",
  "height": 175,
  "heightUnits": "cm | inch",
  "disease": "multiple myeloma | follicular lymphoma | breast cancer | chronic lymphocytic leukemia",
  "country": "US",
  "postalCode": "10001",
  "longitude": -74.006,
  "latitude": 40.7128,
  "geolocation": { "longitude": -74.006, "latitude": 40.7128 },

  "priorTherapy": "None | One line | Two lines | More than two lines of therapy",
  "firstLineTherapy": "vrd",
  "firstLineDate": "2022-03-01",
  "firstLineOutcome": "CR | PR | SD | MRD | PD",
  "secondLineTherapy": "kd",
  "secondLineDate": "2023-01-15",
  "secondLineOutcome": "CR | PR | SD | MRD | PD",
  "laterTherapy": "isa-kd",
  "laterDate": "2024-06-01",
  "laterOutcome": "CR | PR | SD | MRD | PD",
  "laterTherapies": [],

  "stage": "I | II | III | IV",
  "karnofskyPerformanceScore": 80,
  "ecogPerformanceStatus": 1,

  "preExistingConditionCategories": ["cardiacIssues", "pulmonaryDisease"],

  "hemoglobinLevel": 10.5,
  "plateletCount": 150,
  "whiteBloodCellCount": 4.5,
  "serumCreatinineLevel": 1.0,
  "estimatedGlomerularFiltrationRate": 60,
  "liverEnzymeLevelsAlt": 30,
  "liverEnzymeLevelsAst": 25,
  "liverEnzymeLevelsAlp": 80,
  "albuminLevel": 3.5,
  "serumBilirubinLevelTotal": 0.8,
  "serumBilirubinLevelDirect": 0.2,
  "serumCalciumLevel": 9.5,
  "monoclonalProteinSerum": 1.5,
  "monoclonalProteinUrine": 200,
  "lactateDehydrogenaseLevel": 250,

  "geneticMutations": [
    {
      "gene": "tp53",
      "variant": "c.817C>T",
      "origin": "somatic",
      "interpretation": "pathogenic"
    }
  ],

  "stemCellTransplantHistory": "None | completedASCT | eligibleForASCT | ineligibleForASCT | completedAllogeneicSCT | preASCT | postASCT | neverReceivedSCT | sctIneligible | relapsedPostASCT | relapsedPostAllogeneicSCT | completedTandemSCT",
  "plasmaCellLeukemia": false,

  "estrogenReceptorStatus": "er_plus | er_plus_with_hi_exp | er_plus_with_low_exp | er_minus",
  "progesteroneReceptorStatus": "pr_plus | pr_plus_with_hi_exp | pr_plus_with_low_exp | pr_minus",
  "her2Status": "her2_plus | her2_minus",
  "menopausalStatus": "pre | post",
  "tumorStage": "string",
  "pdL1TumorCells": 50,

  "binetStage": "A | B | C",
  "treatmentRefractoryStatus": "notRefractory | primaryRefractory | secondaryRefractory | multiRefractory"
}
```

**Response** `201 Created`: Full `PatientInfo` object with computed fields
(`bmi`, `geo_point`, `tnbcStatus`, `hrStatus`, `treatmentRefractoryStatus`,
etc.).

---

### `GET /patient-info/`

List patient profiles. Optional filter:

| Query param | Description |
|---|---|
| `external_id` | Filter by `externalId` |

---

### `GET /patient-info/{id}/`

Retrieve a single patient profile by primary key.

---

### `PATCH /patient-info/{id}/`

Partial update. Same body shape as `POST`. Only supplied fields are updated;
normalization runs on the full resulting record.

---

### `GET /patient-info/{id}/study-info/`

Retrieve saved search preferences for this patient.

**Response:**
```json
{
  "searchTitle": "My Search",
  "searchDisease": "multiple myeloma",
  "sponsor": "",
  "recruitmentStatus": "RECRUITING",
  "country": "US",
  "distance": 100,
  "distanceUnits": "miles",
  "trialType": ""
}
```

---

### `PATCH /patient-info/{id}/study-info/`

Update saved search preferences. All fields are optional.

---

## Trials

### `GET /trials/`

List trials ordered by match score descending.

**Patient context**: required via `?patient_info_id=` or `"patientInfo"` body.

**Query params:**

| Param | Values | Description |
|---|---|---|
| `type` | `all`, `eligible`, `potential`, `not_eligible` | Filter by match status |
| `search` | string | Full-text search on title fields |

**Response** (paginated, 200 per page by default):
```json
{
  "count": 142,
  "next": "http://…/trials/?page=2",
  "previous": null,
  "results": [
    {
      "trialId": 1,
      "studyId": "NCT03000000",
      "briefTitle": "A Study of Drug X in Myeloma",
      "phase": ["PHASE2"],
      "disease": "Multiple Myeloma",
      "recruitingStatus": "RECRUITING",
      "location": ["New York, NY, USA", "Boston, MA, USA"],
      "distance": 12.3,
      "distanceUnits": "miles",
      "matchScore": 85,
      "matchingType": "eligible",
      "attributesToFillIn": [
        {
          "trialAttributeName": "stem_cell_transplant_history_required",
          "userAttributeName": "stem_cell_transplant_history",
          "userAttributeTitle": "Stem Cell Transplant History",
          "count": 4
        }
      ],
      "goodnessScore": 72,
      "patientBurdenScore": 15,
      "enrollmentCount": 120,
      "sponsor": "BioPharm Inc.",
      "link": "https://clinicaltrials.gov/ct2/show/NCT03000000"
    }
  ]
}
```

---

### `GET /trials/search/`

Extended search endpoint with sorting and filtering.

**Patient context**: required.

**Query params:**

| Param | Values | Default | Description |
|---|---|---|---|
| `type` | `all`, `eligible`, `potential`, `not_eligible`, `favorites` | `all` | Match-status filter |
| `sort` | `goodnessScore`, `matchScore`, `patientBurdenScore`, `distance`, `status`, `phase`, `updated`, `enrollment` | `goodnessScore` | Sort order |
| `view` | template name | — | Override the attribute-detail template |
| `search` | string | — | Full-text search |

---

### `GET /trials/count/`

Returns the count of matched trials without fetching full records.

**Patient context**: required.

**Response:**
```json
{ "count": 37 }
```

---

### `GET /trials/{id}/`

Retrieve full trial details including all eligibility attributes grouped for
display, with per-attribute patient match status.

**Patient context**: required.

**Response:** Full trial object including `trialEligibilityAttributes` grouped
by category, each with the trial's value, the patient's current value, and the
match status (`matched`, `unknown`, or `not_matched`).

---

## Trial graph

### `GET /trials-graph/graph/`

Returns a compact graph-structured response optimised for visual dependency
views.

**Patient context**: required.

**Query params:**

| Param | Default | Description |
|---|---|---|
| `n` | 50 | Maximum number of trial nodes to return |

**Response:**
```json
{
  "trialNodes": [
    {
      "trialId": 1,
      "briefTitle": "A Study of Drug X",
      "matchScore": 85,
      "attributes": {
        "matched": [
          { "label": "Age", "trialValue": "18–65", "patientValue": "52" }
        ],
        "notMatched": [
          { "label": "Gender", "trialValue": "Female only", "patientValue": "M" }
        ],
        "missing": [
          { "label": "Stem Cell Transplant History", "trialValue": "required", "patientValue": null }
        ]
      }
    }
  ]
}
```

---

## Form settings

### `GET /form-settings/`

Returns all dropdown option lists used by patient-intake forms.

**Query params:**

| Param | Description |
|---|---|
| `disease` | If provided, also returns `trialTypes` scoped to this disease |

**Response** (partial example):
```json
{
  "disease": [
    { "value": "multiple myeloma", "label": "Multiple Myeloma" },
    { "value": "follicular lymphoma", "label": "Follicular Lymphoma" },
    { "value": "breast cancer", "label": "Breast Cancer" },
    { "value": "chronic lymphocytic leukemia", "label": "Chronic Lymphocytic Leukemia" }
  ],
  "gender": [
    { "value": "", "label": "Unknown" },
    { "value": "M", "label": "Male" },
    { "value": "F", "label": "Female" }
  ],
  "stemCellTransplantHistory": [ ... ],
  "firstLineTherapy": [ ... ],
  "cytogenicMarkers": [ ... ],
  "molecularMarkers": [ ... ],
  "ethnicity": [ ... ],
  "therapyTypesAll": [ ... ],
  "therapyComponentsAll": [ ... ],
  "trialTypes": [ ... ]
}
```

---

## Lookup tables

### `GET /countries/`

Returns the list of preferred countries for the location picker.

### `GET /locations/`

Returns locations (trial sites). Optional filters:

| Param | Description |
|---|---|
| `country_id` | Filter by country FK |
| `state_id` | Filter by state FK |

---

## Pagination

All list endpoints return a standard paginated envelope:

```json
{
  "count": 200,
  "next": "http://…?page=2",
  "previous": null,
  "results": [ ... ]
}
```

Default page size is 200. Override with `?page_size=<n>`.

---

## Error responses

| Status | When |
|---|---|
| `400 Bad Request` | Validation error or missing required `patient_info_id` / `patientInfo` body |
| `401 Unauthorized` | Missing or invalid auth token |
| `404 Not Found` | Record not found |
| `500 Internal Server Error` | Unexpected server error |

Error body:
```json
{ "detail": "Human-readable error message" }
```

or for field-level validation errors:
```json
{ "fieldName": ["This field is required."] }
```
