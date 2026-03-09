"""
Management command: search_trials_for_omop_patients

Reads PatientInfo records from an exactomop database and calls the exact
Trials Search API for each patient, then writes a summary of results.

Usage:
    python manage.py search_trials_for_omop_patients \\
      --source-db-url postgresql://user:pass@host:5432/exactomop \\
      --api-url http://localhost:8000 \\
      --api-token <your-token>

    # Filter patients and write full JSON output
    python manage.py search_trials_for_omop_patients \\
      --source-db-url $EXACTOMOP_DATABASE_URL \\
      --api-url $EXACT_API_URL \\
      --api-token $EXACT_API_TOKEN \\
      --person-ids 1,2,3 \\
      --output results.json

    # Dry run — print the request body for the first patient
    python manage.py search_trials_for_omop_patients \\
      --source-db-url $EXACTOMOP_DATABASE_URL \\
      --api-url $EXACT_API_URL \\
      --api-token $EXACT_API_TOKEN \\
      --dry-run
"""
import csv
import json
import logging
import os
import sys
from datetime import date

import psycopg2
import psycopg2.extras
import requests

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Columns to skip when building the API request body.
# These are either exactomop-only fields or handled specially below.
# ------------------------------------------------------------------
SKIP_COLUMNS = frozenset({
    # PKs / FKs
    'id', 'person_id',
    # exactomop-only columns not in exact
    'condition_code_icd_10', 'condition_code_snomed_ct',
    'therapy_lines_count', 'line_of_therapy',
    'liver_enzyme_levels', 'serum_bilirubin_level',
    'remission_duration_min', 'washout_period_duration',
    'hiv_status', 'hepatitis_b_status', 'hepatitis_c_status',
    # Replaced by languages_skills in exact
    'languages', 'language_skill_level',
    # Backfill artefact
    'old_supportive_therapies',
    # Geo field — PostGIS only, not in exactomop
    'geo_point',
})

# JSON fields that should be decoded from string if needed
JSON_FIELDS = frozenset({
    'later_therapies', 'supportive_therapies',
    'genetic_mutations', 'stem_cell_transplant_history',
})


def _to_camel_case(snake: str) -> str:
    parts = snake.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def _build_patient_info_body(row: dict) -> dict:
    """Convert an exactomop patient_info DB row to the exact API request body.

    - Skips exactomop-only columns and NULL values
    - Converts snake_case keys to camelCase
    - Ensures JSON fields are proper Python objects (not strings)
    - Converts date objects to ISO strings
    """
    body = {}
    for col, val in row.items():
        if col in SKIP_COLUMNS:
            continue
        if val is None:
            continue

        # Ensure JSON fields are decoded objects
        if col in JSON_FIELDS:
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    val = [val] if val else []
            if not val:  # skip empty lists
                continue

        # Convert date to ISO string
        if isinstance(val, date):
            val = val.isoformat()

        body[_to_camel_case(col)] = val

    return body


class Command(BaseCommand):
    help = (
        'Search exact Trials API for each PatientInfo in an exactomop database '
        'and output matching trial results.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-db-url',
            type=str,
            default=os.environ.get('EXACTOMOP_DATABASE_URL', ''),
            help='PostgreSQL connection URL for the exactomop database. '
                 'Falls back to EXACTOMOP_DATABASE_URL env var.',
        )
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
            help='Number of patients to fetch per DB batch (default: 100)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Max trials to return per patient from the API (default: 50)',
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
        parser.add_argument(
            '--output',
            type=str,
            default='',
            help='Write full JSON results to this file path (default: stdout summary only)',
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

    def handle(self, *args, **options):
        source_db_url = options['source_db_url']
        if not source_db_url:
            self.stderr.write(self.style.ERROR(
                'No source DB URL. Use --source-db-url or set EXACTOMOP_DATABASE_URL.'
            ))
            return

        api_url = options['api_url'].rstrip('/')
        api_token = options['api_token']
        if not api_token and not options['dry_run']:
            self.stderr.write(self.style.ERROR(
                'No API token. Use --api-token or set EXACT_API_TOKEN.'
            ))
            return

        person_ids = []
        if options['person_ids']:
            person_ids = [int(x.strip()) for x in options['person_ids'].split(',') if x.strip()]

        session = requests.Session()
        if api_token:
            session.headers['Authorization'] = f'Token {api_token}'
        session.headers['Content-Type'] = 'application/json'

        all_results = []

        try:
            conn = psycopg2.connect(source_db_url)
        except psycopg2.Error as e:
            self.stderr.write(self.style.ERROR(f'DB connection failed: {e}'))
            return

        processed = 0
        errors = 0

        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = 'SELECT * FROM patient_info'
                params = []
                if person_ids:
                    placeholders = ', '.join(['%s'] * len(person_ids))
                    query += f' WHERE person_id IN ({placeholders})'
                    params = person_ids
                query += ' ORDER BY person_id'
                cursor.execute(query, params)

                while True:
                    rows = cursor.fetchmany(options['batch_size'])
                    if not rows:
                        break

                    for row in rows:
                        person_id = row.get('person_id')
                        external_id = row.get('external_id') or str(person_id)
                        disease = row.get('disease') or ''

                        patient_info_body = _build_patient_info_body(dict(row))

                        if options['dry_run']:
                            self.stdout.write(
                                f'person_id={person_id}, disease={disease}\n'
                                f'Request body:\n'
                                f'{json.dumps({"patient_info": patient_info_body}, indent=2, default=str)}'
                            )
                            return  # show only the first patient then stop

                        try:
                            result = self._search_trials(
                                session, api_url,
                                patient_info_body,
                                limit=options['limit'],
                                sort=options['sort'],
                                benefit_weight=options['benefit_weight'],
                                patient_burden_weight=options['patient_burden_weight'],
                                risk_weight=options['risk_weight'],
                                distance_penalty_weight=options['distance_penalty_weight'],
                            )
                            result['person_id'] = person_id
                            result['external_id'] = external_id
                            result['disease'] = disease
                            all_results.append(result)

                            self._print_patient_summary(result)
                            processed += 1

                            if processed % 10 == 0:
                                self.stdout.write(f'  Processed {processed} patients...')

                        except Exception:
                            errors += 1
                            logger.exception('Error searching trials for person_id=%s', person_id)
                            self.stderr.write(self.style.ERROR(
                                f'  Error for person_id={person_id}'
                            ))

        finally:
            conn.close()

        if not options['dry_run']:
            self.stdout.write(self.style.SUCCESS(
                f'\nDone. Patients processed: {processed}, Errors: {errors}'
            ))

            if options['output']:
                self._write_output(
                    all_results, options['output'], options['output_format']
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Results written to: {options["output"]}'
                ))

    # ------------------------------------------------------------------

    def _search_trials(self, session, api_url, patient_info_body, limit, sort,
                       benefit_weight=25.0, patient_burden_weight=25.0,
                       risk_weight=25.0, distance_penalty_weight=25.0):
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

        resp = session.get(url, params=params, json={'patient_info': patient_info_body}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        trials = data.get('results', [])
        total = data.get('itemsTotalCount', 0)

        eligible = [t for t in trials if t.get('matchingType') == 'eligible']
        potential = [t for t in trials if t.get('matchingType') == 'potential']

        scores = [t.get('matchScore') for t in trials if t.get('matchScore') is not None]
        best_score = max(scores) if scores else None

        return {
            'total_trials': total,
            'returned_trials': len(trials),
            'eligible_count': len(eligible),
            'potential_count': len(potential),
            'best_match_score': best_score,
            'trials': trials,
        }

    def _print_patient_summary(self, result):
        pid = result['person_id']
        eid = result['external_id']
        disease = result['disease'] or '(unknown)'
        total = result['total_trials']
        eligible = result['eligible_count']
        potential = result['potential_count']
        score = result['best_match_score']
        score_str = f'{score}%' if score is not None else 'n/a'

        self.stdout.write(
            f'  person_id={pid} ext={eid} [{disease}] '
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
                'person_id', 'external_id', 'disease',
                'total_trials', 'eligible_count', 'potential_count',
                'best_match_score',
                'top_trial_ids',  # comma-separated NCT IDs of top 5
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
                        'external_id': r['external_id'],
                        'disease': r['disease'],
                        'total_trials': r['total_trials'],
                        'eligible_count': r['eligible_count'],
                        'potential_count': r['potential_count'],
                        'best_match_score': r['best_match_score'],
                        'top_trial_ids': top_ids,
                    })
