import pytest

from trials.services.patient_info.convertors.bilirubin_convertor import BilirubinConvertor


class TestBilirubinConvertor:
    def test_call(self):
        assert round(BilirubinConvertor.call(0.5, 'mg/dl', 'micromoles/l'), 4) == 8.55
