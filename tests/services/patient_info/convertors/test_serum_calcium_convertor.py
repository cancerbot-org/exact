from trials.models import PatientInfo
import pytest

from trials.services.patient_info.convertors.serum_calcium_convertor import SerumCalciumConvertor


class TestSerumCalciumConvertor:
    def test_call(self):
        assert round(SerumCalciumConvertor.call(9.5, 'mg/dl', 'micromoles/l'), 4) == 2.3702
