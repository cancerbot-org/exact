from trials.models import PatientInfo
import pytest

from trials.services.patient_info.convertors.scr_uln_calculator import ScrUlnCalculator
from tests.factories import *


class TestScrUlnCalculator:
    @pytest.mark.django_db
    def test_call(self):
        pi = PatientInfo(ethnicity='Native American', gender='M')
        assert round(ScrUlnCalculator.call(1.55, pi), 2) == 1.19

        pi = PatientInfo(ethnicity='Native American', gender='F')
        assert round(ScrUlnCalculator.call(1.55, pi), 2) == 1.41

        pi = PatientInfo(ethnicity='Native American', gender='')
        assert ScrUlnCalculator.call(1.55, pi) is None

        pi = PatientInfo(ethnicity='', gender='F')
        assert ScrUlnCalculator.call(1.55, pi) is None
