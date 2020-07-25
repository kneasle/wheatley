import unittest

from rr_bot.main import parse_peal_speed, PealSpeedParseError

class ArgParseTests(unittest.TestCase):

    def test_peal_speed_parsing(self):
        self.assertEqual(parse_peal_speed("3h04m"), 184)
        self.assertEqual(parse_peal_speed("10"), 10)
        self.assertEqual(parse_peal_speed("3m"), 3)
        self.assertEqual(parse_peal_speed("3h"), 180)
        self.assertEqual(parse_peal_speed("3 h"), 180)
        self.assertEqual(parse_peal_speed("2h58"), 178)
        self.assertEqual(parse_peal_speed("2h58m"), 178)
        self.assertEqual(parse_peal_speed(" 2 h 30 m "), 150)

        def test_error(input_string, expected_message):
            with self.assertRaises(PealSpeedParseError) as e:
                parse_peal_speed(input_string)

            self.assertEqual(e.exception.message, expected_message)

        test_error("3h4hhh", "The peal speed should contain at most one 'h'.")

        test_error("Xh", "The hour value 'X' is not an integer.")
        test_error("-4h", "The hour value '-4' must be a positive integer.")

        test_error("3hP", "The minute value 'P' is not an integer.")
        test_error("3h-2m", "The minute value '-2' must be a positive integer.")
        test_error("3h100m", "The minute value '100' must be smaller than 60.")

        test_error("125x", "The minute value '125x' is not an integer.")
        test_error("-2m", "The minute value '-2' must be a positive integer.")
        test_error("-200", "The minute value '-200' must be a positive integer.")

        test_error("", "The minute value '' is not an integer.")
        test_error("    ", "The minute value '' is not an integer.")
        test_error("\nXX   X ", "The minute value 'XX   X' is not an integer.")

if __name__ == '__main__':
    unittest.main()
