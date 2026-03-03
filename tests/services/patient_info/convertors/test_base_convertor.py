import pytest

from trials.services.patient_info.convertors.base_convertor import BaseConvertor


class TestBaseConvertor:
    def test_call(self):
        assert round(BaseConvertor.call(80, 'lb', 'kg'), 2) == 36.29
        assert round(BaseConvertor.call(60, "in", "cm"), 2) == 152.4

        assert round(BaseConvertor.call(0.15, "CELLS/UL", "CELLS/L"), 2) == 150000.0
