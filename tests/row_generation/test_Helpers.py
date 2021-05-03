import unittest

from wheatley.row_generation.helpers import (
    convert_bell_string,
    convert_to_bell_string,
    convert_pn,
    generate_starting_row,
)
from wheatley.row_generation.helpers import _CROSS_PN
from wheatley.bell import MAX_BELL, Bell
from wheatley.aliases import Row


class HelpersBellStringTests(unittest.TestCase):
    def test_convert_bell_string(self):
        self.assertEqual(1, convert_bell_string("1"))
        self.assertEqual(9, convert_bell_string("9"))

        self.assertEqual(10, convert_bell_string("0"))
        self.assertEqual(11, convert_bell_string("E"))
        self.assertEqual(12, convert_bell_string("T"))
        self.assertEqual(13, convert_bell_string("A"))
        self.assertEqual(14, convert_bell_string("B"))
        self.assertEqual(15, convert_bell_string("C"))
        self.assertEqual(16, convert_bell_string("D"))

    def test_convert_bell_string_not_found(self):
        with self.assertRaisesRegex(ValueError, "'F' is not known bell symbol"):
            convert_bell_string("F")

    def test_convert_to_bell_string(self):
        self.assertEqual("1", convert_to_bell_string(1))
        self.assertEqual("9", convert_to_bell_string(9))

        self.assertEqual("0", convert_to_bell_string(10))
        self.assertEqual("E", convert_to_bell_string(11))
        self.assertEqual("T", convert_to_bell_string(12))
        self.assertEqual("A", convert_to_bell_string(13))
        self.assertEqual("B", convert_to_bell_string(14))
        self.assertEqual("C", convert_to_bell_string(15))
        self.assertEqual("D", convert_to_bell_string(16))

    def test_convert_to_bell_string_not_found(self):
        with self.assertRaisesRegex(ValueError, "'0' is not known bell number"):
            convert_to_bell_string(0)

        with self.assertRaisesRegex(ValueError, f"'{MAX_BELL + 1}' is not known bell number"):
            convert_to_bell_string(MAX_BELL + 1)


class HelpersPlaceNotationTests(unittest.TestCase):
    def test_convert_pn_unknown_bell(self):
        with self.assertRaisesRegex(ValueError, "'F' is not known bell symbol"):
            place_notation = "&-F"
            convert_pn(place_notation)

    def test_convert_pn(self):
        test_cases = [
            ("&-1", [_CROSS_PN, [1], _CROSS_PN]),
            ("-1", [_CROSS_PN, [1]]),
            ("-123-4", [_CROSS_PN, [1, 2, 3], _CROSS_PN, [4]]),
            ("-1-1,2", [_CROSS_PN, [1], _CROSS_PN, [1], _CROSS_PN, [1], _CROSS_PN, [2]]),
            ("x1", [_CROSS_PN, [1]]),
            ("x.1.-.", [_CROSS_PN, [1], _CROSS_PN]),
            ("12.3-123", [[1, 2], [3], _CROSS_PN, [1, 2, 3]]),
            ("&-1,&2.3", [_CROSS_PN, [1], _CROSS_PN, [2], [3], [2]]),
            ("&-1,2.3", [_CROSS_PN, [1], _CROSS_PN, [2], [3], [2]]),
            ("&-1,+2.3", [_CROSS_PN, [1], _CROSS_PN, [2], [3]]),
            ("-1,&2.3", [_CROSS_PN, [1], _CROSS_PN, [2], [3], [2]]),
            ("-1,2.3", [_CROSS_PN, [1], _CROSS_PN, [2], [3], [2]]),
            ("-1,2.3,4", [_CROSS_PN, [1], _CROSS_PN, [2], [3], [2], [4]]),
            ("---4", [_CROSS_PN, _CROSS_PN, _CROSS_PN, [4]]),
            (".-.-.1.-.2", [_CROSS_PN, _CROSS_PN, [1], _CROSS_PN, [2]]),
        ]

        for (input_pn, expected_output_pn) in test_cases:
            with self.subTest(input_pn=input_pn, expected_output_pn=expected_output_pn):
                self.assertEqual(convert_pn(input_pn), expected_output_pn)


class HelpersGenerateStartingRowTests(unittest.TestCase):
    def test_generate_without_custom_row(self):
        self.assertListEqual(Row([Bell(0), Bell(1), Bell(2), Bell(3)]), generate_starting_row(4))

    def test_generate_with_custom_row(self):
        self.assertListEqual(Row([Bell(3), Bell(2), Bell(1), Bell(0)]), generate_starting_row(4, "4321"))
        self.assertListEqual(Row([Bell(3), Bell(2), Bell(1), Bell(0)]), generate_starting_row(4, "432"))
        self.assertListEqual(Row([Bell(3), Bell(1), Bell(0), Bell(2)]), generate_starting_row(4, "42"))
        self.assertListEqual(Row([Bell(1), Bell(0), Bell(2), Bell(3)]), generate_starting_row(4, "2"))

    def test_generate_with_invalid_custom_row(self):
        with self.assertRaisesRegex(ValueError, "starting row '4324' contains the same bell multiple times"):
            generate_starting_row(4, "4324")


if __name__ == "__main__":
    unittest.main()
