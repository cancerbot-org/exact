from trials.services.patient_info.patient_info import PatientInfo
import pytest

from trials.services.patient_info.convertors.alt_uln_calculator import AltUlnCalculator
from tests.factories import *


class TestAltUlnCalculator:
    @pytest.mark.django_db
    def test_call(self):
        pi = PatientInfo(ethnicity='Native American', gender='M')
        assert round(AltUlnCalculator.call(83, pi), 2) == 1.84

        pi = PatientInfo(ethnicity='Native American', gender='F')
        assert round(AltUlnCalculator.call(83, pi), 2) == 2.44

        pi = PatientInfo(ethnicity='Native American', gender='')
        assert AltUlnCalculator.call(83, pi) is None

        pi = PatientInfo(ethnicity='', gender='F')
        assert AltUlnCalculator.call(83, pi) is None
