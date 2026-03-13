"""
Management command: search_trials_for_ctomop_patients

Reads PatientInfo records from a ctomop database (via direct DB access or the
ctomop REST API) and calls the exact Trials Search API for each patient, then
writes a summary of results.

Source modes
------------
DB mode (default) — recommended when you have direct PostgreSQL access:

    python manage.py search_trials_for_ctomop_patients \\
      --source-db-url postgresql://user:pass@host:5432/ctomop \\
      --api-url http://localhost:8000 \\
      --api-token <exact-token>

    Falls back to CTOMOP_DATABASE_URL env var if --source-db-url is not given.

API mode — use when only HTTP access to ctomop is available:

    python manage.py search_trials_for_ctomop_patients \\
      --use-api \\
      --source-api-url http://ctomop.example.com \\
      --source-api-username admin \\
      --source-api-password secret \\
      --api-url http://localhost:8000 \\
      --api-token <exact-token>

    Falls back to CTOMOP_API_URL / CTOMOP_API_USERNAME / CTOMOP_API_PASSWORD env
    vars when the corresponding flags are omitted.

Common options
--------------
    --person-ids 1,2,3      # optional: filter to specific person IDs
    --batch-size 100        # rows per DB fetch (DB mode only)
    --limit 50              # max trials per patient from exact API
    --sort matchScore
    --benefit-weight 25.0
    --patient-burden-weight 25.0
    --risk-weight 25.0
    --distance-penalty-weight 25.0
    --output results.json   # write full JSON output to file
    --format json|csv
    --dry-run               # print first patient's request body and exit
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

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Columns to skip when building the exact API request body.
# These are ctomop-only / legacy / computed fields that do not map
# to exact's PatientInfo and would confuse the matching engine.
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


def _to_camel_case(snake: str) -> str:
    parts = snake.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def _build_patient_info_body(row: dict) -> dict:
    """Convert a ctomop patient_info row / API dict to the exact API request body.

    - Skips ctomop-only and internal columns
    - Skips NULL / None values
    - Converts snake_case keys to camelCase
    - Ensures JSON fields are proper Python objects
    - Converts date objects to ISO strings
    """
    body = {}
    for col, val in row.items():
        if col in SKIP_COLUMNS:
            continue
        if val is None:
            continue

        if col in JSON_FIELDS:
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    val = [val] if val else []
            if not val:
                continue

        if isinstance(val, date):
            val = val.isoformat()

        if isinstance(val, Decimal):
            val = float(val)

        body[_to_camel_case(col)] = val

    return body


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
            default=os.environ.get('CTOMOP_DATABASE_URL', ''),
            help='PostgreSQL connection URL for the ctomop database. '
                 'Falls back to CTOMOP_DATABASE_URL env var.',
        )

        # --- Source: API mode ---
        parser.add_argument(
            '--use-api',
            action='store_true',
            help='Read patients from the ctomop REST API instead of direct DB access.',
        )
        parser.add_argument(
            '--source-api-url',
            type=str,
            default=os.environ.get('CTOMOP_API_URL', ''),
            help='Base URL of the ctomop API (e.g. http://ctomop.example.com). '
                 'Falls back to CTOMOP_API_URL env var.',
        )
        parser.add_argument(
            '--source-api-username',
            type=str,
            default=os.environ.get('CTOMOP_API_USERNAME', ''),
            help='ctomop API username (Basic auth). Falls back to CTOMOP_API_USERNAME.',
        )
        parser.add_argument(
            '--source-api-password',
            type=str,
            default=os.environ.get('CTOMOP_API_PASSWORD', ''),
            help='ctomop API password (Basic auth). Falls back to CTOMOP_API_PASSWORD.',
        )

        # --- Exact API ---
        parser.add_argument(
            '--api-url',
            type=str,
            default=os.environ.get('EXACT_API_URL', 'http://localhost:8000'),
            help='Base URL of the exact API. Falls back to EXACT_API_URL env var.',
        )
        parser.add_argument(
            '--api-token',
            type=str,
            default=os.environ.get('EXACT_API_TOKEN', ''),
            help='Authentication token for the exact API. '
                 'Falls back to EXACT_API_TOKEN env var.',
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
            help='Max trials to return per patient from the exact API (default: 50)',
        )
        parser.add_argument(
            '--sort',
            type=str,
            default='matchScore',
            choices=[
                'matchScore', 'goodnessScore', 'distance',
                'status', 'phase', 'updated', 'enrollment', 'patientBurdenScore',
            ],
            help='Sort order for trial results (default: matchScore)',
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
        api_url = options['api_url'].rstrip('/')
        api_token = options['api_token']
        if not api_token and not options['dry_run']:
            self.stderr.write(self.style.ERROR(
                'No exact API token. Use --api-token or set EXACT_API_TOKEN.'
            ))
            return

        person_ids = []
        if options['person_ids']:
            person_ids = [int(x.strip()) for x in options['person_ids'].split(',') if x.strip()]

        exact_session = requests.Session()
        if api_token:
            exact_session.headers['Authorization'] = f'Token {api_token}'
        exact_session.headers['Content-Type'] = 'application/json'

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

            patient_info_body = _build_patient_info_body(dict(row))

            if options['dry_run']:
                self.stdout.write(
                    f'person_id={person_id}, disease={disease}\n'
                    f'Request body:\n'
                    f'{json.dumps({"patient_info": patient_info_body}, indent=2, default=str)}'
                )
                return

            try:
                result = self._search_trials(
                    exact_session, api_url,
                    patient_info_body,
                    limit=options['limit'],
                    sort=options['sort'],
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
                result['person_id'] = person_id
                result['disease'] = disease
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
                'No source DB URL. Use --source-db-url or set CTOMOP_DATABASE_URL.'
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
    # Trial search
    # ------------------------------------------------------------------

    def _search_trials(self, session, api_url, patient_info_body, limit, sort,
                       benefit_weight=25.0, patient_burden_weight=25.0,
                       risk_weight=25.0, distance_penalty_weight=25.0,
                       search_title='', recruitment_status='', sponsor='',
                       register='', trial_type='', study_type='', study_id='',
                       validated_only=False, distance=None, distance_units='km',
                       country='', region='', postal_code='',
                       last_update='', first_enrolment=''):
        """Call GET /trials/ with patient_info body. Returns summary dict."""
        url = f'{api_url}/trials/'
        params = {
            'limit': limit,
            'sort': sort,
            'page': 1,
            'benefitWeight': benefit_weight,
            'patientBurdenWeight': patient_burden_weight,
            'riskWeight': risk_weight,
            'distancePenaltyWeight': distance_penalty_weight,
        }
        if search_title:
            params['searchTitle'] = search_title
        if recruitment_status:
            params['recruitmentStatus'] = recruitment_status
        if sponsor:
            params['sponsor'] = sponsor
        if register:
            params['register'] = register
        if trial_type:
            params['trialType'] = trial_type
        if study_type:
            params['studyType'] = study_type
        if study_id:
            params['studyId'] = study_id
        if validated_only:
            params['validatedOnly'] = 'true'
        if distance is not None:
            params['distance'] = distance
            params['distanceUnits'] = distance_units
        if country:
            params['country'] = country
        if region:
            params['region'] = region
        if postal_code:
            params['postalCode'] = postal_code
        if last_update:
            params['lastUpdate'] = last_update
        if first_enrolment:
            params['firstEnrolment'] = first_enrolment

        resp = session.get(url, params=params, json={'patient_info': patient_info_body}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        trials = data.get('results', [])
        total = data.get('itemsTotalCount', 0)

        eligible = [t for t in trials if t.get('matchingType') == 'eligible']
        potential = [t for t in trials if t.get('matchingType') == 'potential']
        scores = [t.get('matchScore') for t in trials if t.get('matchScore') is not None]

        return {
            'total_trials': total,
            'returned_trials': len(trials),
            'eligible_count': len(eligible),
            'potential_count': len(potential),
            'best_match_score': max(scores) if scores else None,
            'trials': trials,
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
