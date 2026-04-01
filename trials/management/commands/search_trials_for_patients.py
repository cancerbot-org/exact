"""
Management command: search_trials_for_patients

Reads PatientInfo records from an external patient database and matches them
against the trials database using the EXACT matching engine in-process — no
web server required.

Usage
-----
    python manage.py search_trials_for_patients \\
      --source-db-url postgresql://user:pass@host:5432/patients

    Falls back to PATIENT_DATABASE_URL env var if --source-db-url is not given.

Common options
--------------
    --person-ids 1,2,3      # optional: filter to specific person IDs
    --patient-limit 100     # max patients to process (default: all)
    --batch-size 100        # rows per DB fetch
    --limit 50              # max trials to return per patient
    --benefit-weight 25.0
    --patient-burden-weight 25.0
    --risk-weight 25.0
    --distance-penalty-weight 25.0
    --output results.json   # write full JSON output to file
    --format json|csv
    --dry-run               # print first patient's parsed data and exit
"""
import csv
import json
import logging
import os
import re
import sys
from datetime import date
from decimal import Decimal
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from trials.services.user_to_trial_attr_matcher import UserToTrialAttrMatcher

logger = logging.getLogger(__name__)


def _parse_db_url(url):
    """
    Parse a postgres[ql]:// URL into individual psycopg2.connect() kwargs.
    Passing keyword args avoids a double-free crash in psycopg2 on macOS/conda
    caused by libpq's internal URL parser conflicting with the system allocator.
    """
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'dbname': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'sslmode': 'require',
    }

# ------------------------------------------------------------------
# Columns to skip when building the PatientInfo object.
# These are source-only / legacy / computed fields that do not map
# to EXACT's PatientInfo and would confuse the matching engine.
# ------------------------------------------------------------------
SKIP_COLUMNS = frozenset({
    # PKs / FKs
    'id', 'person_id', 'person',
    # Timestamps
    'created_at', 'updated_at',
    # PII not needed for trial matching
    'email', 'date_of_birth',
    # Computed by EXACT (do not override)
    'bmi',
    # Legacy columns not present in EXACT
    'condition_code_icd_10', 'condition_code_snomed_ct',
    'therapy_lines_count', 'line_of_therapy',
    # Legacy duplicate lab fields (EXACT uses named variants)
    'liver_enzyme_levels', 'serum_bilirubin_level',
    # Legacy viral flags (EXACT uses no_hiv_status / no_hepatitis_*_status)
    'hiv_status', 'hepatitis_b_status', 'hepatitis_c_status',
    # PostGIS geography field — source uses lat/lon floats instead
    'geo_point',
    # API-only computed fields
    'patient_name', 'age', 'refractory_status',
    # person-table fields added for normalization — not PatientInfo columns
    'gender_source_value', 'gender_concept_id',
})

# JSON fields that may arrive as strings and need decoding
JSON_FIELDS = frozenset({
    'later_therapies', 'supportive_therapies',
    'genetic_mutations', 'stem_cell_transplant_history',
})


_HISTOLOGIC_MAP = {
    'Ductal carcinoma in situ': 'dcis',
    'Invasive ductal carcinoma': 'infiltrating_ductal_carcinoma',
    'Invasive lobular carcinoma': 'infiltrating_lobular_carcinoma',
    'Medullary carcinoma': 'medullary_carcinoma',
    'Mucinous carcinoma': 'mucinous_colloid_carcinoma',
}

_REFRACTORY_MAP = {
    'Responsive': 'notRefractory',
    'Stable': 'notRefractory',
    # CTOMOP doesn't distinguish primary/secondary/multi-refractory — best-guess mapping.
    'Refractory': 'primaryRefractory',
}


def _normalize_ctomop_row(row: dict) -> dict:
    """Normalize a raw CTOMOP patient_info row to EXACT's internal value format.

    Called before _build_in_memory so all downstream filtering sees the right
    code values. Transformations are idempotent — already-normalized values
    pass through unchanged.
    """
    # ── Receptor statuses ──────────────────────────────────────────────
    # HER2: Equivocal (IHC 2+) → her2_low; Unknown → None.
    her2 = row.get('her2_status')
    if her2 == 'Negative':
        row['her2_status'] = 'her2_minus'
    elif her2 == 'Positive':
        row['her2_status'] = 'her2_plus'
    elif her2 == 'Equivocal':
        row['her2_status'] = 'her2_low'
    elif her2 in ('Unknown', ''):
        row['her2_status'] = None

    # ER/PR: EXACT has 4 levels. Business rule: Positive → hi_exp, Borderline → low_exp.
    er = row.get('estrogen_receptor_status')
    if er == 'Negative':
        row['estrogen_receptor_status'] = 'er_minus'
    elif er == 'Positive':
        row['estrogen_receptor_status'] = 'er_plus_with_hi_exp'
    elif er == 'Borderline':
        row['estrogen_receptor_status'] = 'er_plus_with_low_exp'
    elif er in ('Unknown', ''):
        row['estrogen_receptor_status'] = None

    pr = row.get('progesterone_receptor_status')
    if pr == 'Negative':
        row['progesterone_receptor_status'] = 'pr_minus'
    elif pr == 'Positive':
        row['progesterone_receptor_status'] = 'pr_plus_with_hi_exp'
    elif pr == 'Borderline':
        row['progesterone_receptor_status'] = 'pr_plus_with_low_exp'
    elif pr in ('Unknown', ''):
        row['progesterone_receptor_status'] = None

    # ── Histologic type ────────────────────────────────────────────────
    if row.get('histologic_type') in _HISTOLOGIC_MAP:
        row['histologic_type'] = _HISTOLOGIC_MAP[row['histologic_type']]

    # ── Stage — strip trailing sub-stage letter (IIA → II, IIIB → III) ─
    stage = row.get('stage')
    if stage:
        row['stage'] = re.sub(r'[A-C]$', '', stage)

    # ── Treatment refractory status ────────────────────────────────────
    if row.get('treatment_refractory_status') in _REFRACTORY_MAP:
        row['treatment_refractory_status'] = _REFRACTORY_MAP[row['treatment_refractory_status']]

    # ── Genetic mutations — normalize casing / format ──────────────────
    mutations = row.get('genetic_mutations')
    if isinstance(mutations, list):
        normalized = []
        for m in mutations:
            if not isinstance(m, dict):
                normalized.append(m)
                continue
            m = dict(m)
            if m.get('gene'):
                m['gene'] = m['gene'].lower()
            if m.get('interpretation'):
                m['interpretation'] = m['interpretation'].lower().replace(' ', '_')
            if m.get('origin'):
                m['origin'] = m['origin'].lower()
            normalized.append(m)
        row['genetic_mutations'] = normalized

    # ── Lab value fallbacks (CTOMOP uses renamed columns) ─────────────
    if not row.get('hemoglobin_level') and row.get('hemoglobin_g_dl') is not None:
        row['hemoglobin_level'] = row['hemoglobin_g_dl']

    if not row.get('absolute_neutrophile_count') and row.get('anc_thousand_per_ul') is not None:
        row['absolute_neutrophile_count'] = row['anc_thousand_per_ul'] * 1000

    if not row.get('absolute_lymphocyte_count') and row.get('alc_thousand_per_ul') is not None:
        row['absolute_lymphocyte_count'] = row['alc_thousand_per_ul'] * 1000

    if not row.get('lactate_dehydrogenase_level') and row.get('ldh_u_l') is not None:
        row['lactate_dehydrogenase_level'] = row['ldh_u_l']

    # ── Prior therapy — derive from therapy_lines_count ───────────────
    # CTOMOP prior_therapy is binary Yes/No; therapy_lines_count has the detail.
    lines = row.get('therapy_lines_count')
    if lines is not None:
        _lines_map = {0: 'None', 1: 'One line', 2: 'Two lines'}
        row['prior_therapy'] = _lines_map.get(lines, 'More than two lines of therapy')

    # ── Age from date_of_birth ─────────────────────────────────────────
    if not row.get('patient_age') and row.get('date_of_birth'):
        dob = row['date_of_birth']
        if isinstance(dob, date):
            row['patient_age'] = (date.today() - dob).days // 365

    # ── Gender from person.gender_source_value (added by _fetch_via_db) ─
    # gender_source_value is typically 'M' / 'F' in OMOP; fallback to concept IDs.
    if not row.get('gender'):
        gsv = row.get('gender_source_value', '')
        if gsv in ('M', 'F'):
            row['gender'] = gsv
        elif gsv and gsv.lower().startswith('m'):
            row['gender'] = 'M'
        elif gsv and gsv.lower().startswith('f'):
            row['gender'] = 'F'
        else:
            gci = row.get('gender_concept_id')
            if gci == 8507:
                row['gender'] = 'M'
            elif gci == 8532:
                row['gender'] = 'F'

    return row


def _build_patient_info(row: dict):
    """Convert a patient_info row into an in-memory PatientInfo.

    Uses the same normalization pipeline as the web service (normalize_patient_info)
    so all derived fields (BMI, geo_point, refractory_status, tp53_disruption, etc.)
    are computed identically to what the API would produce.
    """
    from trials.services.patient_info.resolve import _build_in_memory

    row = _normalize_ctomop_row(row)

    # Strip source-only columns; decode any JSON-as-string fields
    cleaned = {}
    for col, val in row.items():
        if col in SKIP_COLUMNS:
            continue
        if val is None:
            continue
        if col in JSON_FIELDS and isinstance(val, str):
            try:
                val = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                val = [val] if val else []
        if not val and col in JSON_FIELDS:
            continue
        if isinstance(val, date):
            val = val.isoformat()
        if isinstance(val, Decimal):
            val = float(val)
        cleaned[col] = val

    # _build_in_memory handles snake_case→PatientInfo + normalize_patient_info
    return _build_in_memory(cleaned)


class Command(BaseCommand):
    help = (
        'Read PatientInfo records from an external patient database and match '
        'them against trials using the EXACT matching engine (in-process).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-db-url',
            type=str,
            default=os.environ.get('PATIENT_DATABASE_URL', ''),
            help='PostgreSQL connection URL for the patient database. '
                 'Falls back to PATIENT_DATABASE_URL env var.',
        )

        # --- Filtering ---
        parser.add_argument(
            '--person-ids',
            type=str,
            default='',
            help='Comma-separated person IDs to process (default: all)',
        )
        parser.add_argument(
            '--patient-limit',
            type=int,
            default=None,
            help='Maximum number of patients to process (default: all). '
                 'Applied before --person-ids filtering.',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Rows per DB batch fetch (default: 100)',
        )

        # --- Trial search ---
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Max trials to return per patient (default: 50)',
        )

        # --- Goodness score weights ---
        parser.add_argument(
            '--benefit-weight',
            type=float,
            default=25.0,
            help='Goodness score benefit component weight (default: 25.0)',
        )
        parser.add_argument(
            '--patient-burden-weight',
            type=float,
            default=25.0,
            help='Goodness score patient burden component weight (default: 25.0)',
        )
        parser.add_argument(
            '--risk-weight',
            type=float,
            default=25.0,
            help='Goodness score risk component weight (default: 25.0)',
        )
        parser.add_argument(
            '--distance-penalty-weight',
            type=float,
            default=25.0,
            help='Goodness score distance penalty component weight (default: 25.0)',
        )

        # --- Output ---
        parser.add_argument(
            '--output',
            type=str,
            default='',
            help='Write full results to this file path (default: stdout summary only)',
        )
        parser.add_argument(
            '--format',
            dest='output_format',
            choices=['json', 'csv'],
            default='json',
            help='Output format for --output file (default: json)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print the parsed data for the first patient and exit',
        )

        # --- Study preferences / search filters ---
        parser.add_argument(
            '--search-title',
            type=str,
            default='',
            help='Filter trials by title keyword',
        )
        parser.add_argument(
            '--recruitment-status',
            type=str,
            default='',
            help='Filter by recruitment status (e.g. RECRUITING)',
        )
        parser.add_argument(
            '--sponsor',
            type=str,
            default='',
            help='Filter trials by sponsor name',
        )
        parser.add_argument(
            '--register',
            type=str,
            default='',
            help='Filter by trial register (e.g. ClinicalTrials.gov)',
        )
        parser.add_argument(
            '--trial-type',
            type=str,
            default='',
            help='Filter by trial type',
        )
        parser.add_argument(
            '--study-type',
            type=str,
            default='',
            help='Filter by study type',
        )
        parser.add_argument(
            '--study-id',
            type=str,
            default='',
            help='Filter by specific study ID (e.g. NCT number)',
        )
        parser.add_argument(
            '--validated-only',
            action='store_true',
            help='Return only manually validated trials',
        )
        parser.add_argument(
            '--distance',
            type=float,
            default=None,
            help='Maximum distance from patient location to trial site',
        )
        parser.add_argument(
            '--distance-units',
            type=str,
            default='km',
            choices=['km', 'miles'],
            help='Distance units: km or miles (default: km)',
        )
        parser.add_argument(
            '--country',
            type=str,
            default='',
            help='Filter trials to a specific country code (e.g. US, DE)',
        )
        parser.add_argument(
            '--region',
            type=str,
            default='',
            help='Filter trials to a specific region/state',
        )
        parser.add_argument(
            '--postal-code',
            type=str,
            default='',
            help='Filter trials near a postal code',
        )
        parser.add_argument(
            '--last-update',
            type=str,
            default='',
            help='Filter trials updated after this date (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--first-enrolment',
            type=str,
            default='',
            help='Filter trials with first enrolment after this date (YYYY-MM-DD)',
        )

    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        person_ids = []
        if options['person_ids']:
            person_ids = [int(x.strip()) for x in options['person_ids'].split(',') if x.strip()]

        rows = self._fetch_via_db(options, person_ids)

        if rows is None:
            return  # error already reported

        all_results = []
        processed = 0
        errors = 0

        for row in rows:
            person_id = row.get('person_id')
            disease = row.get('disease') or ''

            if not disease:
                self.stdout.write(f'  Skipping person_id={person_id} (no disease set)')
                continue

            if options['dry_run']:
                self.stdout.write(
                    f'person_id={person_id}, disease={disease}\n'
                    f'Row keys: {list(row.keys())}'
                )
                return

            try:
                result = self._search_trials_direct(
                    row=dict(row),
                    person_id=person_id,
                    disease=disease,
                    limit=options['limit'],
                    benefit_weight=options['benefit_weight'],
                    patient_burden_weight=options['patient_burden_weight'],
                    risk_weight=options['risk_weight'],
                    distance_penalty_weight=options['distance_penalty_weight'],
                    search_title=options['search_title'],
                    recruitment_status=options['recruitment_status'],
                    sponsor=options['sponsor'],
                    register=options['register'],
                    trial_type=options['trial_type'],
                    study_type=options['study_type'],
                    study_id=options['study_id'],
                    validated_only=options['validated_only'],
                    distance=options['distance'],
                    distance_units=options['distance_units'],
                    country=options['country'],
                    region=options['region'],
                    postal_code=options['postal_code'],
                    last_update=options['last_update'],
                    first_enrolment=options['first_enrolment'],
                )
                all_results.append(result)
                self._print_patient_summary(result)
                processed += 1

                if processed % 10 == 0:
                    self.stdout.write(f'  Processed {processed} patients...')

            except Exception:
                errors += 1
                logger.exception('Error searching trials for person_id=%s', person_id)
                self.stderr.write(self.style.ERROR(f'  Error for person_id={person_id}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Patients processed: {processed}, Errors: {errors}'
        ))

        if options['output']:
            self._write_output(all_results, options['output'], options['output_format'])
            self.stdout.write(self.style.SUCCESS(f'Results written to: {options["output"]}'))

    # ------------------------------------------------------------------
    # Source: DB
    # ------------------------------------------------------------------

    def _fetch_via_db(self, options, person_ids):
        """Yield rows from the patient_info table via psycopg2."""
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            self.stderr.write(self.style.ERROR(
                'psycopg2 is required. Install it with: pip install psycopg2-binary'
            ))
            return None

        source_db_url = options['source_db_url']
        if not source_db_url:
            self.stderr.write(self.style.ERROR(
                'No source DB URL. Use --source-db-url or set PATIENT_DATABASE_URL.'
            ))
            return None

        try:
            conn = psycopg2.connect(**_parse_db_url(source_db_url))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'DB connection failed: {e}'))
            return None

        rows = []
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = '''
                    SELECT pi.*,
                           p.gender_source_value,
                           p.gender_concept_id
                    FROM patient_info pi
                    JOIN person p ON pi.person_id = p.person_id
                '''
                params = []
                if person_ids:
                    placeholders = ', '.join(['%s'] * len(person_ids))
                    query += f' WHERE p.person_id IN ({placeholders})'
                    params = person_ids
                query += ' ORDER BY p.person_id'
                if options.get('patient_limit'):
                    query += ' LIMIT %s'
                    params = list(params) + [options['patient_limit']]

                cursor.execute(query, params)

                while True:
                    batch = cursor.fetchmany(options['batch_size'])
                    if not batch:
                        break
                    rows.extend(dict(r) for r in batch)
        finally:
            conn.close()

        return rows

    # ------------------------------------------------------------------
    # Direct trial search (in-process, no HTTP)
    # ------------------------------------------------------------------

    def _search_trials_direct(self, row: dict, person_id, disease, limit: int,
                               benefit_weight=25.0, patient_burden_weight=25.0,
                               risk_weight=25.0, distance_penalty_weight=25.0,
                               search_title='', recruitment_status='', sponsor='',
                               register='', trial_type='', study_type='', study_id='',
                               validated_only=False, distance=None, distance_units='km',
                               country='', region='', postal_code='',
                               last_update='', first_enrolment=''):
        """Match trials against a patient row using the EXACT ORM directly.

        Pipeline:
          1. _build_patient_info() → normalize_patient_info()
          2. Trial.objects.filtered_trials() — eligibility queryset
          3. with_goodness_score_optimized() — scoring
          4. UserToTrialAttrMatcher — eligible/potential classification
        """
        from trials.models import Trial
        from trials.services.study_preferences import StudyPreferences

        pi = _build_patient_info(row)

        study_prefs = StudyPreferences(
            search_title=search_title or None,
            sponsor=sponsor or None,
            register=register or None,
            study_id=study_id or None,
            trial_type=trial_type or None,
            study_type=study_type or None,
            recruitment_status=recruitment_status or None,
            country=country or None,
            region=region or None,
            postal_code=postal_code or None,
            distance=distance,
            distance_units=distance_units,
            validated_only=validated_only,
            last_update=last_update or None,
            first_enrolment=first_enrolment or None,
        )

        queryset = Trial.objects.all()
        queryset, _ = queryset.filtered_trials(
            search_options={},
            study_info=study_prefs,
            patient_info=pi,
            add_traces=False,
        )
        queryset = queryset.with_goodness_score_optimized(
            benefit_weight=benefit_weight,
            patient_burden_weight=patient_burden_weight,
            risk_weight=risk_weight,
            distance_penalty_weight=distance_penalty_weight,
        )

        total = queryset.count()
        trials_page = list(queryset[:limit])

        eligible = []
        potential = []
        scores = []
        trials_out = []

        for trial in trials_page:
            matcher = UserToTrialAttrMatcher(trial=trial, patient_info=pi)
            match_type = matcher.trial_match_status()
            if match_type == 'not_eligible':
                continue
            match_score = matcher.trial_match_score()
            goodness_score = getattr(trial, 'goodness_score', None)
            if match_score is not None:
                scores.append(match_score)
            trial_data = {
                'studyId': trial.study_id,
                'briefTitle': trial.brief_title,
                'officialTitle': trial.official_title,
                'matchingType': match_type,
                'matchScore': match_score,
                'goodnessScore': goodness_score,
                'recruitmentStatus': trial.recruitment_status,
                'phase': trial.phases,
                'studyType': trial.study_type,
                'sponsor': trial.sponsor_name,
                'link': trial.link,
                'disease': trial.disease,
                'register': trial.register,
            }
            trials_out.append(trial_data)
            if match_type == 'eligible':
                eligible.append(trial_data)
            else:
                potential.append(trial_data)

        return {
            'person_id': person_id,
            'disease': disease,
            'total_trials': total,
            'returned_trials': len(trials_page),
            'eligible_count': len(eligible),
            'potential_count': len(potential),
            'best_match_score': max(scores) if scores else None,
            'eligible_trials': eligible,
            'potential_trials': potential,
            'trials': trials_out,
        }

    def _print_patient_summary(self, result):
        pid = result['person_id']
        disease = result['disease'] or '(unknown)'
        total = result['total_trials']
        eligible = result['eligible_count']
        potential = result['potential_count']
        score = result['best_match_score']
        score_str = f'{score}%' if score is not None else 'n/a'

        self.stdout.write(
            f'  person_id={pid} [{disease}] '
            f'→ {total} total | {eligible} eligible | {potential} potential '
            f'| best score: {score_str}'
        )

    def _write_output(self, results, path, fmt):
        if fmt == 'json':
            with open(path, 'w') as f:
                json.dump(results, f, indent=2, default=str)

        elif fmt == 'csv':
            if not results:
                return
            fieldnames = [
                'person_id', 'disease',
                'total_trials', 'eligible_count', 'potential_count',
                'best_match_score', 'top_trial_ids',
            ]
            with open(path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    top_ids = ','.join(
                        t.get('studyId', '') for t in r.get('trials', [])[:5]
                    )
                    writer.writerow({
                        'person_id': r['person_id'],
                        'disease': r['disease'],
                        'total_trials': r['total_trials'],
                        'eligible_count': r['eligible_count'],
                        'potential_count': r['potential_count'],
                        'best_match_score': r['best_match_score'],
                        'top_trial_ids': top_ids,
                    })
