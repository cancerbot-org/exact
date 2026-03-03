import pytest

from trials.services.patient_info.convertors.bili_d_uln_calculator import BiliDUlnCalculator
from tests.factories import *


class TestBiliDUlnCalculator:
    @pytest.mark.django_db
    def test_call(self):
        pi = PatientInfoFactory(ethnicity='Native American')
        assert round(BiliDUlnCalculator.call(0.45, pi), 2) == 1.5

        pi = PatientInfoFactory(ethnicity='Asian')
        assert round(BiliDUlnCalculator.call(0.45, pi), 2) == 1.29

        pi = PatientInfoFactory(ethnicity='')
        assert BiliDUlnCalculator.call(0.45, pi) is None
