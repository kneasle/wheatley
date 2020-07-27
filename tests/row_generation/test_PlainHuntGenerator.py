import unittest
from unittest import TestCase

from wheatley.row_generation import PlainHuntGenerator
from . import gen_rows


class PlainHuntGeneratorTests(TestCase):

    def test_reset_handstroke(self):
        stage = 3
        generator = PlainHuntGenerator(stage)

        initial_rows = gen_rows(generator, 4)
        self.assertEqual([[2, 1, 3, 4],
                          [2, 3, 1, 4],
                          [3, 2, 1, 4],
                          [3, 1, 2, 4]],
                         initial_rows)
        generator.reset()
        # Starts again after rounds
        second_rows = gen_rows(generator, 4)
        self.assertEqual([[2, 1, 3, 4],
                          [2, 3, 1, 4],
                          [3, 2, 1, 4],
                          [3, 1, 2, 4]],
                         second_rows)

    def test_singles(self):
        stage = 3
        generator = PlainHuntGenerator(stage)
        rows = gen_rows(generator, 6)
        self.assertEqual([[2, 1, 3, 4],
                          [2, 3, 1, 4],
                          [3, 2, 1, 4],
                          [3, 1, 2, 4],
                          [1, 3, 2, 4],
                          [1, 2, 3, 4]],
                         rows)

    def test_minimus(self):
        stage = 4
        generator = PlainHuntGenerator(stage)

        rows = gen_rows(generator, 8)
        self.assertEqual([[2, 1, 4, 3],
                          [2, 4, 1, 3],
                          [4, 2, 3, 1],
                          [4, 3, 2, 1],
                          [3, 4, 1, 2],
                          [3, 1, 4, 2],
                          [1, 3, 2, 4],
                          [1, 2, 3, 4]],
                         rows)

    def test_cinques(self):
        stage = 11
        generator = PlainHuntGenerator(stage)

        rows = gen_rows(generator, 3)
        self.assertEqual([[2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 11, 12],
                          [2, 4, 1, 6, 3, 8, 5, 10, 7, 11, 9, 12],
                          [4, 2, 6, 1, 8, 3, 10, 5, 11, 7, 9, 12]],
                         rows)

    def test_maximus(self):
        stage = 12
        generator = PlainHuntGenerator(stage)

        rows = gen_rows(generator, 3)
        self.assertEqual([[2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11],
                          [2, 4, 1, 6, 3, 8, 5, 10, 7, 12, 9, 11],
                          [4, 2, 6, 1, 8, 3, 10, 5, 12, 7, 11, 9]],
                         rows)


if __name__ == '__main__':
    unittest.main()
