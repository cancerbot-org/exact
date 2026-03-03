import pytest

from trials.services.patient_info.convertors.serum_creatinine_convertor import SerumCreatinineConvertor


class TestSerumCreatinineConvertor:
    def test_call(self):
        assert round(SerumCreatinineConvertor.call(1.2, 'mg/dl', 'micromoles/l'), 4) == 106.104
