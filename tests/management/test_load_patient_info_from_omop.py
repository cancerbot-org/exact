"""
Tests for _build_field_dict logic in load_patient_info_from_omop.

No DB access needed — the mapping is pure Python.
"""
import json
from datetime import date
from unittest.mock import MagicMock

import pytest

from trials.management.commands.load_patient_info_from_omop import (
    NON_NULLABLE_BOOL_DEFAULTS,
    SKIP_SOURCE_COLUMNS,
    Command,
)


@pytest.fixture
def cmd():
    """Command instance with _exact_fields pre-populated from the real model."""
    from trials.models import PatientInfo

    c = Command()
    c.stdout = MagicMock()
    c.stderr = MagicMock()
    c.style = MagicMock()
    c._exact_fields = {f.name for f in PatientInfo._meta.get_fields() if hasattr(f, 'column')}
    return c


class TestSkipSourceColumns:
    def test_person_id_skipped(self, cmd):
        row = {'person_id': 42, 'year_of_birth': 1970}
        result = cmd._build_field_dict(row)
        assert 'person_id' in SKIP_SOURCE_COLUMNS
        assert 'person_id' not in result

    def test_omop_only_columns_skipped(self, cmd):
        row = {
            'person_id': 1,
            'year_of_birth': 1970,
            'condition_code_icd_10': 'C50',
            'condition_code_snomed_ct': '363346000',
            'therapy_lines_count': 3,
            'line_of_therapy': '2L',
            'liver_enzyme_levels': 45,
            'serum_bilirubin_level': '1.2',
            'remission_duration_min': '6 months',
            'washout_period_duration': '2 weeks',
            'hiv_status': True,
            'hepatitis_b_status': False,
            'hepatitis_c_status': False,
            'supportive_therapies': None,
        }
        result = cmd._build_field_dict(row)
        for col in (
            'condition_code_icd_10', 'condition_code_snomed_ct',
            'therapy_lines_count', 'line_of_therapy',
            'liver_enzyme_levels', 'serum_bilirubin_level',
            'remission_duration_min', 'washout_period_duration',
            'hiv_status', 'hepatitis_b_status', 'hepatitis_c_status',
        ):
            assert col not in result, f'{col} should be excluded'


class TestLanguagesMapping:
    def test_both_present(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': 'English', 'language_skill_level': 'fluent',
               'supportive_therapies': None}
        result = cmd._build_field_dict(row)
        assert result['languages_skills'] == 'English - fluent'

    def test_language_only(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': 'Spanish', 'language_skill_level': None,
               'supportive_therapies': None}
        result = cmd._build_field_dict(row)
        assert result['languages_skills'] == 'Spanish'

    def test_both_missing(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None}
        result = cmd._build_field_dict(row)
        assert result['languages_skills'] is None

    def test_whitespace_stripped(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': '  en  ', 'language_skill_level': '  B2  ',
               'supportive_therapies': None}
        result = cmd._build_field_dict(row)
        assert result['languages_skills'] == 'en - B2'


class TestSupportiveTherapiesMapping:
    def test_none_becomes_empty_list(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None}
        result = cmd._build_field_dict(row)
        assert result['supportive_therapies'] == []

    def test_valid_json_list_string(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': '["metformin", "aspirin"]'}
        result = cmd._build_field_dict(row)
        assert result['supportive_therapies'] == ['metformin', 'aspirin']

    def test_json_string_scalar_wrapped(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': '"metformin"'}
        result = cmd._build_field_dict(row)
        assert result['supportive_therapies'] == ['metformin']

    def test_plain_text_wrapped(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': 'metformin'}
        result = cmd._build_field_dict(row)
        assert result['supportive_therapies'] == ['metformin']

    def test_already_a_list_passthrough(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': ['metformin', 'aspirin']}
        result = cmd._build_field_dict(row)
        assert result['supportive_therapies'] == ['metformin', 'aspirin']


class TestYearOfBirthFallback:
    def test_computes_age_when_patient_age_missing(self, cmd):
        row = {'person_id': 1, 'year_of_birth': 1984,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None,
               'patient_age': None}
        result = cmd._build_field_dict(row)
        expected_age = date.today().year - 1984
        assert result['patient_age'] == expected_age

    def test_patient_age_from_source_takes_priority(self, cmd):
        row = {'person_id': 1, 'year_of_birth': 1984,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None,
               'patient_age': 45}
        result = cmd._build_field_dict(row)
        assert result['patient_age'] == 45

    def test_no_year_of_birth_no_age_set(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None,
               'patient_age': None}
        result = cmd._build_field_dict(row)
        assert result.get('patient_age') is None


class TestNonNullableBooleanCoalescing:
    def test_null_coalesced_to_true_default(self, cmd):
        # no_other_active_malignancies defaults to True
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None,
               'no_other_active_malignancies': None}
        result = cmd._build_field_dict(row)
        assert result['no_other_active_malignancies'] is True

    def test_null_coalesced_to_false_default(self, cmd):
        # bone_only_metastasis_status defaults to False
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None,
               'bone_only_metastasis_status': None}
        result = cmd._build_field_dict(row)
        assert result['bone_only_metastasis_status'] is False

    def test_explicit_false_preserved(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None,
               'no_other_active_malignancies': False}
        result = cmd._build_field_dict(row)
        assert result['no_other_active_malignancies'] is False

    def test_all_bool_defaults_applied(self, cmd):
        """Every NON_NULLABLE_BOOL_DEFAULTS field is coalesced when None."""
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None}
        for field in NON_NULLABLE_BOOL_DEFAULTS:
            row[field] = None

        result = cmd._build_field_dict(row)
        for field, default in NON_NULLABLE_BOOL_DEFAULTS.items():
            assert result[field] == default, f'{field}: expected {default}, got {result[field]}'


class TestPlasmaCallLeukemia:
    def test_none_becomes_false(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None,
               'plasma_cell_leukemia': None}
        result = cmd._build_field_dict(row)
        assert result['plasma_cell_leukemia'] is False

    def test_true_preserved(self, cmd):
        row = {'person_id': 1, 'year_of_birth': None,
               'languages': None, 'language_skill_level': None,
               'supportive_therapies': None,
               'plasma_cell_leukemia': True}
        result = cmd._build_field_dict(row)
        assert result['plasma_cell_leukemia'] is True
