import unittest
from zeva12can import BMS12

# Placeholder for future unit tests

class TestBms12(unittest.TestCase):

    def test_unit_from_arbid(self):
        arbid = 310
        expected = 1
        unit = BMS12.unit_from_arbid(arbid)
        assert(unit == expected)

    def test_unit_bad_arbid(self):
        unit = BMS12.unit_from_arbid(299)
        assert(unit is None)

    def test_type_from_arbid(self):
        arbid = 353
        expected = 3
        thetype = BMS12.type_from_arbid(arbid)
        assert(thetype == expected)

if __name__ == "__main__":
    unittest.main()
