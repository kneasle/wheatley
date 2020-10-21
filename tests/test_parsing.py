import unittest

from wheatley.parsing import parse_peal_speed, PealSpeedParseError, parse_call, CallParseError
from wheatley.aliases import CallDef


class ParseTests(unittest.TestCase):

    def test_peal_speed_parsing(self):
        test_cases = [("3h04m", 184),
                      ("10", 10),
                      ("3m", 3),
                      ("3h", 180),
                      ("3 h", 180),
                      ("2h58", 178),
                      ("2h58m", 178),
                      (" 2 h 30 m ", 150)]

        for (input_arg, expected_minutes) in test_cases:
            with self.subTest(input=input_arg, expected_minutes=expected_minutes):
                self.assertEqual(expected_minutes, parse_peal_speed(input_arg))

    def test_peal_speed_parsing_errors(self):
        test_cases = [("3h4hhh", "The peal speed should contain at most one 'h'."),
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
                      ("\nXX   X ", "The minute value 'XX   X' is not an integer.")]

        for (input_arg, expected_message) in test_cases:
            with self.subTest(input=input_arg, expected_message=expected_message):
                with self.assertRaises(PealSpeedParseError) as e:
                    parse_peal_speed(input_arg)
                self.assertEqual(expected_message, e.exception.message)

    def test_call_parsing(self):
        test_cases = [("14", {0: '14'}),
                      ("3.123", {0: '3.123'}),
                      ("  0 \t:  \n 16   ", {0: '16'}),
                      ("20: 70", {20: '70'}),
                      ("20: 70/ 14", {20: '70', 0: '14'})]

        for (input_arg, expected_call_dict) in test_cases:
            with self.subTest(input=input_arg, expected_call_dict=expected_call_dict):
                self.assertEqual(CallDef(expected_call_dict), parse_call(input_arg))

    def test_call_parsing_errors(self):
        test_cases = [("xx:14", "Location 'xx' is not an integer."),
                      ("", "Place notation strings cannot be empty."),
                      ("  /  /    ", "Place notation strings cannot be empty."),
                      ("14/ 1234  ", "Location 0 has two conflicting calls: '14' and '1234'."),
                      (":::  /", "Call specification ':::' should contain at most one ':'.")]

        for (input_arg, expected_message) in test_cases:
            with self.subTest(input=input_arg, expected_message=expected_message):
                with self.assertRaises(CallParseError) as e:
                    parse_call(input_arg)
                self.assertEqual(expected_message, e.exception.message)


if __name__ == '__main__':
    unittest.main()
