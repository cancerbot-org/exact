import json
import logging
import os
from datetime import date

import psycopg2
import psycopg2.extras

from django.core.management.base import BaseCommand

from trials.models import PatientInfo
from trials.services.patient_info.normalize import normalize_patient_info

logger = logging.getLogger(__name__)

# Source columns to skip in the generic field-copy loop.
# These are either exactomop-only (no matching exact field) or need special handling.
SKIP_SOURCE_COLUMNS = frozenset({
    # Primary keys / foreign keys
    'person_id', 'id',
    # exactomop-only columns (not in exact model)
    'condition_code_icd_10', 'condition_code_snomed_ct',
    'therapy_lines_count', 'line_of_therapy',
    'liver_enzyme_levels', 'serum_bilirubin_level',
    'remission_duration_min', 'washout_period_duration',
    'hiv_status', 'hepatitis_b_status', 'hepatitis_c_status',
    # From person table join
    'year_of_birth',
    # Special mapping (languages + language_skill_level -> languages_skills)
    'languages', 'language_skill_level',
    # Type conversion (TextField -> JSONField)
    'supportive_therapies',
})

# Non-nullable boolean fields in exact with their model defaults.
# exactomop may store NULL for these; coalesce to the model default.
NON_NULLABLE_BOOL_DEFAULTS = {
    'no_other_active_malignancies': True,
    'pulmonary_function_test_result': False,
    'bone_imaging_result': False,
    'consent_capability': True,
    'caregiver_availability_status': False,
    'contraceptive_use': False,
    'no_pregnancy_or_lactation_status': True,
    'pregnancy_test_result': False,
    'no_mental_health_disorder_status': True,
    'no_concomitant_medication_status': True,
    'no_tobacco_use_status': True,
    'no_substance_use_status': True,
    'no_geographic_exposure_risk': True,
    'no_hiv_status': True,
    'no_hepatitis_b_status': True,
    'no_hepatitis_c_status': True,
    'no_active_infection_status': True,
    'bone_only_metastasis_status': False,
    'measurable_disease_by_recist_status': False,
}


class Command(BaseCommand):
    help = 'Load PatientInfo records from an exactomop database into exact'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-db-url',
            type=str,
            default=os.environ.get('EXACTOMOP_DATABASE_URL', ''),
            help='PostgreSQL connection URL for the exactomop database. '
                 'Falls back to EXACTOMOP_DATABASE_URL env var.',
        )
        parser.add_argument(
            '--person-ids',
            type=str,
            default='',
            help='Comma-separated person IDs to load (default: all)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of rows to fetch per batch (default: 100)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Log field mapping without writing to the database',
        )

    def handle(self, *args, **options):
        source_db_url = options['source_db_url']
        if not source_db_url:
            self.stderr.write(self.style.ERROR(
                'No source database URL provided. '
                'Use --source-db-url or set EXACTOMOP_DATABASE_URL.'
            ))
            return

        person_ids = []
        if options['person_ids']:
            person_ids = [
                int(x.strip())
                for x in options['person_ids'].split(',')
                if x.strip()
            ]

        batch_size = options['batch_size']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN mode — no records will be written'))

        # Cache PatientInfo concrete field names for validation
        self._exact_fields = {
            f.name for f in PatientInfo._meta.get_fields()
            if hasattr(f, 'column')
        }

        created_count = 0
        updated_count = 0
        error_count = 0

        try:
            conn = psycopg2.connect(source_db_url)
        except psycopg2.Error as e:
            self.stderr.write(self.style.ERROR(f'Failed to connect to source database: {e}'))
            return

        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = """
                    SELECT pi.*, p.year_of_birth
                    FROM patient_info pi
                    JOIN person p ON pi.person_id = p.person_id
                """
                params = []
                if person_ids:
                    placeholders = ', '.join(['%s'] * len(person_ids))
                    query += f' WHERE p.person_id IN ({placeholders})'
                    params = person_ids

                query += ' ORDER BY pi.person_id'
                cursor.execute(query, params)

                while True:
                    rows = cursor.fetchmany(batch_size)
                    if not rows:
                        break

                    for row in rows:
                        person_id = row['person_id']
                        try:
                            field_dict = self._build_field_dict(dict(row))
                            external_id = str(person_id)

                            if dry_run:
                                self.stdout.write(
                                    f'  person_id={person_id}:\n'
                                    f'{json.dumps(field_dict, indent=2, default=str)}'
                                )
                                continue

                            result = self._upsert_patient(external_id, field_dict)
                            if result == 'created':
                                created_count += 1
                            else:
                                updated_count += 1

                            total = created_count + updated_count
                            if total % 50 == 0:
                                self.stdout.write(
                                    f'  Progress: {created_count} created, '
                                    f'{updated_count} updated'
                                )

                        except Exception:
                            error_count += 1
                            logger.exception(
                                'Error processing person_id=%s', person_id
                            )
                            self.stderr.write(self.style.ERROR(
                                f'  Error processing person_id={person_id}'
                            ))
        finally:
            conn.close()

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'Done. Created: {created_count}, Updated: {updated_count}, '
                f'Errors: {error_count}'
            ))

    # ------------------------------------------------------------------
    # Field mapping
    # ------------------------------------------------------------------

    def _build_field_dict(self, row):
        """Map an exactomop source row to a PatientInfo field dict."""
        field_dict = {}

        # 1) Generic copy: columns with the same name in both databases
        for col, val in row.items():
            if col in SKIP_SOURCE_COLUMNS:
                continue
            if col in self._exact_fields:
                field_dict[col] = val

        # 2) languages + language_skill_level -> languages_skills
        lang = (row.get('languages') or '').strip()
        level = (row.get('language_skill_level') or '').strip()
        if lang or level:
            parts = [p for p in (lang, level) if p]
            field_dict['languages_skills'] = ' - '.join(parts)
        else:
            field_dict['languages_skills'] = None

        # 3) supportive_therapies: TextField -> JSONField
        raw_st = row.get('supportive_therapies')
        if raw_st and isinstance(raw_st, str):
            try:
                parsed = json.loads(raw_st)
                field_dict['supportive_therapies'] = (
                    parsed if isinstance(parsed, list) else [parsed]
                )
            except (json.JSONDecodeError, TypeError):
                field_dict['supportive_therapies'] = [raw_st]
        elif isinstance(raw_st, list):
            field_dict['supportive_therapies'] = raw_st
        else:
            field_dict['supportive_therapies'] = []

        # 4) year_of_birth -> patient_age (fallback when patient_age is missing)
        if not field_dict.get('patient_age') and row.get('year_of_birth'):
            field_dict['patient_age'] = date.today().year - row['year_of_birth']

        # 5) Non-nullable boolean coalescing (None -> model default)
        for field_name, default_val in NON_NULLABLE_BOOL_DEFAULTS.items():
            if field_name in field_dict and field_dict[field_name] is None:
                field_dict[field_name] = default_val

        # 6) Non-nullable JSONField defaults
        if 'genetic_mutations' in field_dict:
            val = field_dict['genetic_mutations']
            if val is None:
                field_dict['genetic_mutations'] = []
            elif isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    field_dict['genetic_mutations'] = (
                        parsed if isinstance(parsed, list) else [parsed]
                    )
                except (json.JSONDecodeError, TypeError):
                    field_dict['genetic_mutations'] = []

        # 7) stem_cell_transplant_history: ensure valid JSON type
        if 'stem_cell_transplant_history' in field_dict:
            val = field_dict['stem_cell_transplant_history']
            if isinstance(val, str):
                try:
                    field_dict['stem_cell_transplant_history'] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    field_dict['stem_cell_transplant_history'] = (
                        [val] if val else []
                    )

        # 8) plasma_cell_leukemia: exactomop has wrong default (True)
        if field_dict.get('plasma_cell_leukemia') is None:
            field_dict['plasma_cell_leukemia'] = False

        return field_dict

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    def _upsert_patient(self, external_id, field_dict):
        """Create or update a PatientInfo record.

        On create, calls normalize_patient_info() explicitly since the
        pre_save signal skips normalization for new (pk-less) instances.
        On update, the pre_save signal handles normalization automatically.

        Returns 'created' or 'updated'.
        """
        try:
            pi = PatientInfo.objects.get(external_id=external_id)
            for key, val in field_dict.items():
                setattr(pi, key, val)
            pi.save()
            return 'updated'
        except PatientInfo.DoesNotExist:
            pi = PatientInfo(external_id=external_id, **field_dict)
            normalize_patient_info(pi)
            pi.save()
            return 'created'
