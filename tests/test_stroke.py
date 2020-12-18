import unittest
from wheatley.stroke import Stroke, HANDSTROKE, BACKSTROKE


class StrokeTests(unittest.TestCase):
    def test_equality(self):
        for i in [True, False]:
            for j in [True, False]:
                # Strokes containing `i` and `j` should be equal precisely when `i == j`
                self.assertEqual(Stroke(i) == Stroke(j), i == j)
                # Strokes containing `i` and `j` should be not equal precisely when `i != j`
                self.assertEqual(Stroke(i) != Stroke(j), i != j)

    def test_constants(self):
        self.assertEqual(HANDSTROKE, Stroke(True))
        self.assertEqual(BACKSTROKE, Stroke(False))

    def test_is_hand(self):
        self.assertEqual(HANDSTROKE.is_hand(), True)
        self.assertEqual(BACKSTROKE.is_hand(), False)

    def test_is_back(self):
        self.assertEqual(HANDSTROKE.is_back(), False)
        self.assertEqual(BACKSTROKE.is_back(), True)

    def test_from_index(self):
        stroke = HANDSTROKE
        for i in range(-100, 100):
            self.assertEqual(Stroke.from_index(i), stroke)
            stroke = stroke.opposite()

    def test_opposite(self):
        self.assertEqual(HANDSTROKE.opposite(), BACKSTROKE)
        self.assertEqual(BACKSTROKE.opposite(), HANDSTROKE)

    def test_to_string(self):
        self.assertEqual(str(HANDSTROKE), 'HANDSTROKE')
        self.assertEqual(str(BACKSTROKE), 'BACKSTROKE')

    def test_to_char(self):
        self.assertEqual(HANDSTROKE.char(), 'H')
        self.assertEqual(BACKSTROKE.char(), 'B')


if __name__ == '__main__':
    unittest.main()
