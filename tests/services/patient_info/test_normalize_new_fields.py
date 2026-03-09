"""
Tests for _normalize_measurable_disease_imwg and related normalize logic
added for new fields.
"""
import pytest

from trials.services.patient_info.normalize import normalize_patient_info
from tests.factories import *


class TestNormalizeMeasurableDiseaseImwg:
    """Tests for _normalize_measurable_disease_imwg via normalize_patient_info."""

    @pytest.mark.django_db
    def test_serum_m_protein_above_threshold(self):
        pi = PatientInfoFactory(monoclonal_protein_serum=0.5)
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is True

    @pytest.mark.django_db
    def test_serum_m_protein_below_threshold(self):
        pi = PatientInfoFactory(monoclonal_protein_serum=0.4)
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is False

    @pytest.mark.django_db
    def test_urine_m_protein_above_threshold(self):
        pi = PatientInfoFactory(monoclonal_protein_urine=200)
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is True

    @pytest.mark.django_db
    def test_urine_m_protein_below_threshold(self):
        pi = PatientInfoFactory(monoclonal_protein_urine=199)
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is False

    @pytest.mark.django_db
    def test_kappa_lambda_abnormal_ratio_and_high_flc(self):
        # ratio = 0.1 (< 0.26), kappa_flc = 100 → True
        pi = PatientInfoFactory(kappa_flc=100, lambda_flc=1000)
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is True

    @pytest.mark.django_db
    def test_kappa_lambda_normal_ratio(self):
        # ratio = 1.0 (within 0.26–1.65) → False
        pi = PatientInfoFactory(kappa_flc=50, lambda_flc=50)
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is False

    @pytest.mark.django_db
    def test_kappa_lambda_abnormal_ratio_but_flc_below_threshold(self):
        # ratio = 0.1 (< 0.26), but both FLC < 100 → False
        pi = PatientInfoFactory(kappa_flc=9, lambda_flc=90)
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is False

    @pytest.mark.django_db
    def test_all_source_values_missing_yields_false(self):
        # normalize always sets measurable_disease_imwg — False when no criteria met
        pi = PatientInfoFactory(
            monoclonal_protein_serum=None,
            monoclonal_protein_urine=None,
            kappa_flc=None,
            lambda_flc=None,
        )
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is False

    @pytest.mark.django_db
    def test_any_true_component_wins(self):
        # serum below threshold, urine above → True
        pi = PatientInfoFactory(monoclonal_protein_serum=0.1, monoclonal_protein_urine=300)
        normalize_patient_info(pi)
        assert pi.measurable_disease_imwg is True
