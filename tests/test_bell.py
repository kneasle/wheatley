import unittest
from wheatley.bell import Bell, BELL_NAMES, MAX_BELL


class BellTests(unittest.TestCase):
    def test_to_from_string_success(self):
        for name in BELL_NAMES:
            with self.subTest(name=name):
                self.assertEqual(str(Bell.from_str(name)), name)

    def test_from_string_error(self):
        for name in ['p', 'a', 'x', 'O', '?', '14', 'q1', '00']:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    Bell.from_str(name)

    def test_from_index_success(self):
        for i in range(MAX_BELL):
            self.assertEqual(Bell.from_index(i).index, i)

    def test_from_index_error(self):
        for i in [-1, MAX_BELL, MAX_BELL + 1, 100, -1100]:
            with self.assertRaises(ValueError):
                Bell.from_index(i)
        # This should be disallowed by the type checker, but may as well test that it does fail
        with self.assertRaises(TypeError):
            Bell.from_index(None)

    def test_from_number_success(self):
        for i in range(1, MAX_BELL + 1):
            self.assertEqual(Bell.from_number(i).number, i)

    def test_from_number_error(self):
        for i in [-1, 0, MAX_BELL + 1, MAX_BELL + 2, 100, -1100]:
            with self.assertRaises(ValueError):
                Bell.from_number(i)
        # This should be disallowed by the type checker, but may as well test that it does fail
        with self.assertRaises(TypeError):
            Bell.from_number(None)

    def test_equality(self):
        for i in range(MAX_BELL):
            for j in range(MAX_BELL):
                # Bells with indices `i` and `j` should be equal precisely when `i == j`
                self.assertEqual(Bell.from_index(i) == Bell.from_index(j), i == j)
                # Bells with indices `i` and `j` should be not equal precisely when `i != j`
                self.assertEqual(Bell.from_index(i) != Bell.from_index(j), i != j)


if __name__ == '__main__':
    unittest.main()
