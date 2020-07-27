import unittest

from wheatley.row_generation.helpers import convert_bell_string, convert_to_bell_string, convert_pn
from wheatley.row_generation.helpers import _CROSS_PN


class HelpersBellStringTests(unittest.TestCase):
    def test_convert_bell_string(self):
        self.assertEqual(1, convert_bell_string("1"))
        self.assertEqual(9, convert_bell_string("9"))

        self.assertEqual(10, convert_bell_string("0"))
        self.assertEqual(11, convert_bell_string("E"))
        self.assertEqual(12, convert_bell_string("T"))

    def test_convert_bell_string_not_found(self):
        with self.assertRaisesRegex(ValueError, "'A' is not known bell symbol"):
            convert_bell_string("A")

    def test_convert_to_bell_string(self):
        self.assertEqual("1", convert_to_bell_string(1))
        self.assertEqual("9", convert_to_bell_string(9))

        self.assertEqual("0", convert_to_bell_string(10))
        self.assertEqual("E", convert_to_bell_string(11))
        self.assertEqual("T", convert_to_bell_string(12))

    def test_convert_to_bell_string_not_found(self):
        with self.assertRaisesRegex(ValueError, "'0' is not known bell number"):
            convert_to_bell_string(0)

        with self.assertRaisesRegex(ValueError, "'13' is not known bell number"):
            convert_to_bell_string(13)


class HelpersPlaceNotationTests(unittest.TestCase):
    def test_convert_pn_unknown_bell(self):
        with self.assertRaisesRegex(ValueError, "'A' is not known bell symbol"):
            place_notation = "&-A"
            convert_pn(place_notation)

    def test_convert_pn_symmetric(self):
        place_notation = "&-1"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1], _CROSS_PN], result)

    def test_convert_pn_asymmetric(self):
        place_notation = "-1"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1]], result)

    def test_convert_pn_multiple_bells(self):
        place_notation = "-123-4"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1, 2, 3], _CROSS_PN, [4]], result)

    def test_convert_pn_x(self):
        place_notation = "x1"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1]], result)

    def test_convert_pn_dot(self):
        place_notation = "x.1.-."
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1], _CROSS_PN], result)

    def test_convert_pn_multiple_bells_and_dots(self):
        place_notation = "12.3-123"
        result = convert_pn(place_notation)
        self.assertEqual([[1, 2], [3], _CROSS_PN, [1, 2, 3]], result)

    def test_convert_pn_multiple_sections_both_symmetric(self):
        place_notation = "&-1,&2.3"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1], _CROSS_PN, [2], [3], [2]], result)

    def test_convert_pn_multiple_sections_first_symmetric(self):
        place_notation = "&-1,2.3"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1], _CROSS_PN, [2], [3]], result)

    def test_convert_pn_multiple_sections_second_symmetric(self):
        place_notation = "-1,&2.3"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1], [2], [3], [2]], result)

    def test_convert_pn_multiple_sections_neither_symmetric(self):
        place_notation = "-1,2.3"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1], [2], [3]], result)

    def test_convert_pn_multiple_sections_3(self):
        place_notation = "-1,2.3,4"
        result = convert_pn(place_notation)
        self.assertEqual([_CROSS_PN, [1], [2], [3], [4]], result)


if __name__ == '__main__':
    unittest.main()
