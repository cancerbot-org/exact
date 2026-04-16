"""
Management command to probe eligibility of specific trials for specific patients.

Uses psql CLI (not psycopg2 directly) to avoid the double-free crash on macOS/conda
when a second psycopg2 connection is opened while Django's own connection is active.

Usage:
    python manage.py probe_eligibility --person-id 20300 --trial-id 18502
    python manage.py probe_eligibility --person-id 20298 --trial-id 43159
"""
import json
import os
import subprocess

from django.core.management.base import BaseCommand

from trials.management.commands.search_trials_for_patients import _build_patient_info
from trials.management.commands.compare_trials import _psql_query_one
from trials.models import Trial


class Command(BaseCommand):
    help = 'Probe why a trial is eligible or ineligible for a patient (add_traces).'

    def add_arguments(self, parser):
        parser.add_argument('--person-id', type=int, required=True)
        parser.add_argument('--trial-id', type=int, required=True)
        parser.add_argument(
            '--source-db-url',
            default=os.environ.get('PATIENT_DATABASE_URL', ''),
        )

    def handle(self, *args, **options):
        db_url = options['source_db_url']
        person_id = options['person_id']
        trial_id = options['trial_id']

        row = _psql_query_one(db_url, f'''
            SELECT pi.*, p.given_name, p.family_name,
                   p.gender_source_value, p.gender_concept_id
            FROM patient_info pi
            JOIN person p ON pi.person_id = p.person_id
            WHERE pi.person_id = {person_id}
            LIMIT 1
        ''')

        pi = _build_patient_info(dict(row))

        name = f"{row.get('given_name', '')} {row.get('family_name', '')}".strip()
        self.stdout.write(f'\n=== {name} (person_id={person_id}) ===')
        self.stdout.write(f'  geo_point           : {pi.geo_point}')
        self.stdout.write(f'  prior_therapy       : {pi.prior_therapy!r}')
        self.stdout.write(f'  her2_status         : {pi.her2_status!r}')
        self.stdout.write(f'  estrogen_receptor   : {pi.estrogen_receptor_status!r}')
        self.stdout.write(f'  progesterone_recep  : {pi.progesterone_receptor_status!r}')
        self.stdout.write(f'  hr_status           : {pi.hr_status!r}')
        self.stdout.write(f'  histologic_type     : {pi.histologic_type!r}')
        self.stdout.write(f'  stage               : {pi.stage!r}')
        self.stdout.write(f'  first_line_therapy  : {pi.first_line_therapy!r}')
        self.stdout.write(f'  second_line_therapy : {pi.second_line_therapy!r}')
        self.stdout.write(f'  treatment_refractory: {pi.treatment_refractory_status!r}')

        _, traces = (
            Trial.objects.using('trials')
            .filter(id=trial_id)
            .filter_by_patient_info(pi, add_traces=True)
        )

        dropped = [t for t in traces if t.get('dropped', 0) > 0]

        if dropped:
            self.stdout.write(f'\nTrial {trial_id} → INELIGIBLE. Dropped by:')
            for t in dropped:
                attr = t['attr'].replace('patient_info.', '')
                self.stdout.write(f'  {attr:42s} val={t["val"]!r}  dropped={t["dropped"]}')
        else:
            self.stdout.write(f'\nTrial {trial_id} → ELIGIBLE (passes all filters)')
