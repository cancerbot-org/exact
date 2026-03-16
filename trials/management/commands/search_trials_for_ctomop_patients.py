"""
Management command: search_trials_for_ctomop_patients

Reads PatientInfo records directly from a ctomop database (or ctomop REST API)
and matches them against the trials database using the EXACT matching engine
in-process — no web server required.

Source modes
------------
DB mode (default):

    python manage.py search_trials_for_ctomop_patients \\
      --source-db-url postgresql://user:pass@host:5432/ctomop

    Falls back to PATIENT_DATABASE_URL env var if --source-db-url is not given.


Common options
--------------
    --person-ids 1,2,3      # optional: filter to specific person IDs
    --batch-size 100        # rows per DB fetch (DB mode only)
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
import sys
from datetime import date
from decimal import Decimal

import requests

from django.core.management.base import BaseCommand
from trials.services.user_to_trial_attr_matcher import UserToTrialAttrMatcher

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Columns to skip when building the PatientInfo object.
# These are ctomop-only / legacy / computed fields that do not map
# to EXACT's PatientInfo and would confuse the matching engine.
# ------------------------------------------------------------------
SKIP_COLUMNS = frozenset({
    # PKs / FKs
    'id', 'person_id', 'person',
    # Timestamps
    'created_at', 'updated_at',
    # PII not needed for trial matching
    'email', 'date_of_birth',
    # Computed by exact (do not override)
    'bmi',
    # ctomop legacy columns not present in exact
    'condition_code_icd_10', 'condition_code_snomed_ct',
    'therapy_lines_count', 'line_of_therapy',
    # Legacy duplicate lab fields (exact uses named variants)
    'liver_enzyme_levels', 'serum_bilirubin_level',
    # Legacy viral flags (exact uses no_hiv_status / no_hepatitis_*_status)
    'hiv_status', 'hepatitis_b_status', 'hepatitis_c_status',
    # PostGIS geography field — ctomop uses lat/lon floats instead
    'geo_point',
    # API-only computed fields from PatientInfoSerializer
    'patient_name', 'age', 'refractory_status',
})

# JSON fields that may arrive as strings and need decoding
JSON_FIELDS = frozenset({
    'later_therapies', 'supportive_therapies',
    'genetic_mutations', 'stem_cell_transplant_history',
})


def _build_patient_info(row: dict):
    """Convert a ctomop patient_info row directly into an in-memory PatientInfo.

    Uses the same normalization pipeline as the web service (normalize_patient_info)
    so all derived fields (BMI, geo_point, refractory_status, tp53_disruption, etc.)
    are computed identically to what the API would produce.
    """
    from trials.services.patient_info.resolve import _build_in_memory

    # Strip ctomop-only columns; decode any JSON-as-string fields
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
        'Search exact Trials API for each PatientInfo in a ctomop database '
        '(direct DB or ctomop REST API) and output matching trial results.'
    )

    def add_arguments(self, parser):
        # --- Source: DB mode (default) ---
        parser.add_argument(
            '--source-db-url',
            type=str,
            default=os.environ.get('PATIENT_DATABASE_URL', ''),
            help='PostgreSQL connection URL for the ctomop database. '
                 'Falls back to PATIENT_DATABASE_URL env var.',
        )

        # --- Source: API mode ---
        parser.add_argument(
            '--use-api',
            action='store_true',
            help='Read patients from the ctomop REST API instead of direct DB access.',
        )

        # --- Filtering ---
        parser.add_argument(
            '--person-ids',
            type=str,
            default='',
            help='Comma-separated person IDs to process (default: all)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Rows per DB batch fetch — DB mode only (default: 100)',
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
            help='Print the API request body for the first patient and exit',
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

        if options['use_api']:
            rows = self._fetch_via_api(options, person_ids)
        else:
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
    # Source: DB mode
    # ------------------------------------------------------------------

    def _fetch_via_db(self, options, person_ids):
        """Yield rows from ctomop's patient_info table via psycopg2."""
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            self.stderr.write(self.style.ERROR(
                'psycopg2 is required for DB mode. Install it with: pip install psycopg2-binary'
            ))
            return None

        source_db_url = options['source_db_url']
        if not source_db_url:
            self.stderr.write(self.style.ERROR(
                'No source DB URL. Use --source-db-url or set PATIENT_DATABASE_URL.'
            ))
            return None

        try:
            conn = psycopg2.connect(source_db_url)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'DB connection failed: {e}'))
            return None

        rows = []
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Join person to get person_id for display / filtering
                query = '''
                    SELECT pi.*
                    FROM patient_info pi
                    JOIN person p ON pi.person_id = p.person_id
                '''
                params = []
                if person_ids:
                    placeholders = ', '.join(['%s'] * len(person_ids))
                    query += f' WHERE p.person_id IN ({placeholders})'
                    params = person_ids
                query += ' ORDER BY p.person_id'

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
    # Source: API mode
    # ------------------------------------------------------------------

    def _fetch_via_api(self, options, person_ids):
        """Fetch full PatientInfo records from ctomop's REST API."""
        source_api_url = options['source_api_url'].rstrip('/')
        username = options['source_api_username']
        password = options['source_api_password']

        if not source_api_url:
            self.stderr.write(self.style.ERROR(
                'No ctomop API URL. Use --source-api-url or set CTOMOP_API_URL.'
            ))
            return None
        if not username or not password:
            self.stderr.write(self.style.ERROR(
                'ctomop API requires Basic auth credentials. '
                'Use --source-api-username / --source-api-password '
                'or set CTOMOP_API_USERNAME / CTOMOP_API_PASSWORD.'
            ))
            return None

        session = requests.Session()
        session.auth = (username, password)

        # Step 1: list all patients to get their PKs
        list_url = f'{source_api_url}/api/patient-info/'
        try:
            resp = session.get(list_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f'ctomop API list request failed: {e}'))
            return None

        entries = resp.json()
        if isinstance(entries, dict):
            # Handle DRF paginated response
            entries = entries.get('results', [])

        if person_ids:
            person_id_set = set(person_ids)
            entries = [e for e in entries if e.get('person_id') in person_id_set]

        if not entries:
            self.stdout.write('No patients found.')
            return []

        self.stdout.write(f'Fetching full data for {len(entries)} patients from ctomop API...')

        rows = []
        for entry in entries:
            pk = entry.get('id')
            person_id = entry.get('person_id')
            if pk is None:
                self.stderr.write(self.style.WARNING(
                    f'Skipping entry without id (person_id={person_id})'
                ))
                continue

            try:
                detail_resp = session.get(f'{source_api_url}/api/patient-info/{pk}/', timeout=30)
                detail_resp.raise_for_status()
                row = detail_resp.json()
                # Ensure person_id is available for filtering / logging
                row.setdefault('person_id', person_id)
                rows.append(row)
            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(
                    f'Failed to fetch patient id={pk} (person_id={person_id}): {e}'
                ))

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
        """Match trials against a ctomop patient row using the EXACT ORM directly.

        This replicates the full web-service pipeline in-process:
          1. _build_patient_info() → normalize_patient_info() — same derived-field
             computation as the API (BMI, geo_point, tp53_disruption, etc.)
          2. Trial.objects.filtered_trials() — identical eligibility queryset
          3. with_goodness_score_optimized() — identical scoring
          4. trial.matching_type(pi) — identical eligible/potential classification
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
            # 'not_eligible' means filtered_trials() shouldn't have returned it, skip
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
