import unittest

from wheatley.parsing import (
    parse_peal_speed,
    PealSpeedParseError,
    parse_call,
    CallParseError,
    parse_start_row,
    StartRowParseError,
    parse_place_notation,
    PlaceNotationError,
)
from wheatley.aliases import CallDef
from wheatley.row_generation.complib_composition_generator import parse_arg, InvalidComplibURLError


class ParseTests(unittest.TestCase):
    def test_peal_speed_parsing(self):
        test_cases = [
            ("3h04m", 184),
            ("10", 10),
            ("3m", 3),
            ("3h", 180),
            ("3 h", 180),
            ("2h58", 178),
            ("2h58m", 178),
            (" 2 h 30 m ", 150),
        ]

        for input_arg, expected_minutes in test_cases:
            with self.subTest(input=input_arg, expected_minutes=expected_minutes):
                self.assertEqual(expected_minutes, parse_peal_speed(input_arg))

    def test_peal_speed_parsing_errors(self):
        test_cases = [
            ("3h4hhh", "The peal speed should contain at most one 'h'."),
            ("Xh", "The hour value 'X' is not an integer."),
            ("-4h", "The hour value '-4' must be a positive integer."),
            ("3hP", "The minute value 'P' is not an integer."),
            ("3h-2m", "The minute value '-2' must be a positive integer."),
            ("3h100", "The minute value '100' must be smaller than 60."),
            ("125x", "The minute value '125x' is not an integer."),
            ("-2m", "The minute value '-2' must be a positive integer."),
            ("-200", "The minute value '-200' must be a positive integer."),
            ("", "The minute value '' is not an integer."),
            ("    ", "The minute value '' is not an integer."),
            ("\nXX   X ", "The minute value 'XX   X' is not an integer."),
        ]

        for input_arg, expected_message in test_cases:
            with self.subTest(input=input_arg, expected_message=expected_message):
                with self.assertRaises(PealSpeedParseError) as e:
                    parse_peal_speed(input_arg)
                self.assertEqual(expected_message, e.exception.message)

    def test_call_parsing(self):
        test_cases = [
            ("14", {0: "14"}),
            ("3.123", {0: "3.123"}),
            ("  0 \t:  \n 16   ", {0: "16"}),
            ("20: 70", {20: "70"}),
            ("20: 70/ 14", {20: "70", 0: "14"}),
        ]

        for input_arg, expected_call_dict in test_cases:
            with self.subTest(input=input_arg, expected_call_dict=expected_call_dict):
                self.assertEqual(CallDef(expected_call_dict), parse_call(input_arg))

    def test_call_parsing_errors(self):
        test_cases = [
            ("xx:14", "Location 'xx' is not an integer."),
            ("", "Place notation strings cannot be empty."),
            ("  /  /    ", "Place notation strings cannot be empty."),
            ("14/ 1234  ", "Location 0 has two conflicting calls: '14' and '1234'."),
            (":::  /", "Call specification ':::' should contain at most one ':'."),
        ]

        for input_arg, expected_message in test_cases:
            with self.subTest(input=input_arg, expected_message=expected_message):
                with self.assertRaises(CallParseError) as e:
                    parse_call(input_arg)
                self.assertEqual(expected_message, e.exception.message)

    def test_place_notation_parsing(self):
        test_cases = [("5:5.1.5.1.5", (5, "5.1.5.1.5")), ("6:x16,12", (6, "x16,12"))]

        for input_arg, expected_tuple in test_cases:
            with self.subTest(input=input_arg, expected_tuple=expected_tuple):
                self.assertEqual(expected_tuple, parse_place_notation(input_arg))

    def test_place_notation_parsing_errors(self):
        test_cases = [
            ("x16x16x16,12", "<stage>:<place notation> required"),
            ("x:x16x16x16,12", "Stage must be a number"),
            ("6:z16x16x16,12", "Place notation is invalid"),
        ]

        for input_arg, expected_message in test_cases:
            with self.subTest(input=input_arg, expected_message=expected_message):
                with self.assertRaises(PlaceNotationError) as e:
                    parse_place_notation(input_arg)
                self.assertEqual(expected_message, e.exception.message)

    def test_url_conversion_public(self):
        # All of these test cases should point to comp #73916, with no access key
        test_cases = [
            "https://complib.org/composition/73916",
            "http://complib.org/composition/73916",
            "http://www.complib.org/composition/73916",
            "complib.org/composition/73916",
            "73916",
            "http://www.complib.org/composition/73916/rows",
            "api.complib.org/composition/73916/rows",
            "http://www.api.complib.org/composition/73916",
            "https://www.api.complib.org/composition/73916/rows",
        ]
        for input_url in test_cases:
            with self.subTest(input=input_url):
                _id, key, substituted_method_id = parse_arg(input_url)
                self.assertEqual(_id, 73916)
                self.assertEqual(key, None)
                self.assertEqual(substituted_method_id, None)

    def test_url_conversion_private(self):
        # All of these test cases should point to comp #65575, with access key "8b9f...da5d"
        test_cases = [
            "https://complib.org/composition/65575?accessKey=8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d",
            "complib.org/composition/65575/rows?accessKey=8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d",
            "www.complib.org/composition/65575?accessKey=8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d",
            "www.complib.org/composition/65575/rows?accessKey=8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d",
            "www.api.complib.org/composition/65575/rows?accessKey=8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d",
            "https://www.api.complib.org/composition/65575/rows?accessKey=8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d",
            "api.complib.org/composition/65575?accessKey=8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d",
            "65575?accessKey=8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d",
        ]
        for input_url in test_cases:
            with self.subTest(input=input_url):
                _id, key, substituted_method_id = parse_arg(input_url)
                self.assertEqual(_id, 65575)
                self.assertEqual(key, "8b9fcc4fb35c428c31e711f657a3e4aac1b3da5d")
                self.assertEqual(substituted_method_id, None)

    def test_url_conversion_subst_method(self):
        test_cases = [
            "https://complib.org/composition/36532?substitutedmethodid=20336",
            "complib.org/composition/36532?substitutedmethodid=20336",
            "www.complib.org/composition/36532?substitutedmethodid=20336",
            "https://www.complib.org/composition/36532?substitutedmethodid=20336",
            "https://www.api.complib.org/composition/36532/rows?substitutedmethodid=20336",
            "api.complib.org/composition/36532/rows?substitutedmethodid=20336",
            "36532?substitutedmethodid=20336",
        ]
        for input_url in test_cases:
            with self.subTest(input=input_url):
                _id, key, substituted_method_id = parse_arg(input_url)
                self.assertEqual(_id, 36532)
                self.assertEqual(key, None)
                self.assertEqual(substituted_method_id, 20336)

    def test_url_conversion_priv_subst_method(self):
        test_cases = [
            "https://complib.org/composition/51155?substitutedmethodid=27600&accessKey=9e1fcd2b11435552cf236be93c7ff73058870995",
            "https://www.complib.org/composition/51155?substitutedmethodid=27600&accessKey=9e1fcd2b11435552cf236be93c7ff73058870995",
            "api.complib.org/composition/51155?substitutedmethodid=27600&accessKey=9e1fcd2b11435552cf236be93c7ff73058870995",
            "complib.org/composition/51155?substitutedmethodid=27600&accessKey=9e1fcd2b11435552cf236be93c7ff73058870995",
            "https://complib.org/composition/51155?accessKey=9e1fcd2b11435552cf236be93c7ff73058870995&substitutedmethodid=27600",
            "https://api.complib.org/composition/51155/rows?accessKey=9e1fcd2b11435552cf236be93c7ff73058870995&substitutedmethodid=27600",
            "https://complib.org/composition/51155/rows?accessKey=9e1fcd2b11435552cf236be93c7ff73058870995&substitutedmethodid=27600",
            "51155?substitutedmethodid=27600&accessKey=9e1fcd2b11435552cf236be93c7ff73058870995",
        ]
        for input_url in test_cases:
            with self.subTest(input=input_url):
                _id, key, substituted_method_id = parse_arg(input_url)
                self.assertEqual(_id, 51155)
                self.assertEqual(key, "9e1fcd2b11435552cf236be93c7ff73058870995")
                self.assertEqual(substituted_method_id, 27600)

    def test_url_conversion_errors(self):
        test_cases = [
            ("complib.org/method/12345", "Not a composition."),
            ("", "Composition ID '' is not a number."),
            ("complib.org", "URL needs more path segments."),
            ("complib.org/composition", "URL needs more path segments."),
            (
                "complib.org/composition/36532?substitutedmethodid=",
                "Substituted method ID '' is not a number.",
            ),
            ("36532?substitutedmethodid=", "Substituted method ID '' is not a number."),
            ("?substitutedmethodid=pengtekkas", "Composition ID '' is not a number."),
        ]
        for input_url, exp_err_str in test_cases:
            with self.subTest(input=input_url, exp_err_str=exp_err_str):
                with self.assertRaisesRegex(InvalidComplibURLError, exp_err_str):
                    parse_arg(input_url)

    def test_parse_start_row(self):
        test_cases = [("654321", 6), ("1", 1)]

        for input_arg, expected_output in test_cases:
            with self.subTest(input=input_arg, expected_output=expected_output):
                output = parse_start_row(input_arg)
                self.assertEqual(output, expected_output)

    def test_parse_start_row_errors(self):
        test_cases = [
            ("6", "Start row does not contain bell(s) [1, 2, 3, 4, 5]"),
            ("64321", "Start row does not contain bell(s) [5]"),
            ("4321G", "'G' is not known bell symbol"),
            ("654326", "Start row contains bell 6 mutiple times"),
        ]

        for input_arg, expected_message in test_cases:
            with self.subTest(input=input_arg, expected_message=expected_message):
                with self.assertRaises(StartRowParseError) as e:
                    parse_start_row(input_arg)
                self.assertEqual(expected_message, e.exception.message)


if __name__ == "__main__":
    unittest.main()
