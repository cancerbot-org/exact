from trials.models import PatientInfo
import pytest

from tests.factories import *
from trials.services.patient_info.convertors.ast_uln_calculator import AstUlnCalculator


class TestAstUlnCalculator:
    @pytest.mark.django_db
    def test_call(self):
        pi = PatientInfo(ethnicity='Native American', gender='M')
        assert round(AstUlnCalculator.call(83, pi), 2) == 2.08

        pi = PatientInfo(ethnicity='Native American', gender='F')
        assert round(AstUlnCalculator.call(83, pi), 2) == 2.37

        pi = PatientInfo(ethnicity='Native American', gender='')
        assert AstUlnCalculator.call(83, pi) is None

        pi = PatientInfo(ethnicity='', gender='F')
        assert AstUlnCalculator.call(83, pi) is None
