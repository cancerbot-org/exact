from trials.models import PatientInfo
import pytest

from trials.services.patient_info.convertors.bili_t_uln_calculator import BiliTUlnCalculator
from tests.factories import *


class TestBiliTUlnCalculator:
    @pytest.mark.django_db
    def test_call(self):
        pi = PatientInfo(ethnicity='Native American')
        assert round(BiliTUlnCalculator.call(1.55, pi), 2) == 1.29

        pi = PatientInfo(ethnicity='Asian')
        assert round(BiliTUlnCalculator.call(1.55, pi), 2) == 1.19

        pi = PatientInfo(ethnicity='')
        assert BiliTUlnCalculator.call(1.55, pi) is None
