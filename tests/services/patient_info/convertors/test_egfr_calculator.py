from trials.models import PatientInfo
import pytest

from trials.services.patient_info.convertors.egfr_calculator import EgfrCalculator
from tests.factories import *


class TestEgfrCalculator:
    @pytest.mark.django_db
    def test_call(self):
        pi = PatientInfo(patient_age=50, gender='M', serum_creatinine_level=1.1)
        assert EgfrCalculator.call(pi) == 81.78

        pi = PatientInfo(patient_age=50, gender='F', serum_creatinine_level=1.1)
        assert EgfrCalculator.call(pi) == 61.22

        pi = PatientInfo(patient_age=40, gender='F', serum_creatinine_level=1.1)
        assert EgfrCalculator.call(pi) == 65.14

        pi = PatientInfo(patient_age=40, gender='F', serum_creatinine_level=101.1, serum_creatinine_level_units='micromoles/l')
        assert EgfrCalculator.call(pi) == 62.19

        pi = PatientInfo(patient_age=40, gender='F', serum_creatinine_level=101.1, serum_creatinine_level_units='dummy')
        assert EgfrCalculator.call(pi) == 62.19

        pi = PatientInfo(patient_age=40, gender='F', serum_creatinine_level=None)
        assert EgfrCalculator.call(pi) is None

        pi = PatientInfo(patient_age=40, gender=None, serum_creatinine_level=1.1)
        assert EgfrCalculator.call(pi) is None

        pi = PatientInfo(patient_age=None, gender='F', serum_creatinine_level=1.1)
        assert EgfrCalculator.call(pi) is None
