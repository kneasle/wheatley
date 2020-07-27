from unittest import TestCase

from tests.row_generation import as_bells
from wheatley.row_generation import DixonoidsGenerator


class DixonoidsGeneratorTests(TestCase):

    def test_dixons_treble_leading_handstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Backstroke previous
        previous_row = as_bells([1, 4, 3, 2, 5, 6])
        new_row = generator._gen_row(previous_row, is_handstroke=True, index=0)
        self.assertEqual(as_bells([4, 1, 2, 3, 6, 5]), new_row)

    def test_dixons_treble_leading_backstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Handstroke previous
        previous_row = as_bells([1, 3, 2, 4, 6, 5])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(as_bells([1, 3, 4, 2, 5, 6]), new_row)

    def test_dixons_treble_leading_backstroke_bob(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        generator.set_bob()
        # Handstroke previous
        previous_row = as_bells([1, 3, 2, 4, 6, 5])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(as_bells([1, 2, 3, 4, 5, 6]), new_row)

    def test_dixons_treble_leading_backstroke_single(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        generator.set_single()
        # Handstroke previous
        previous_row = as_bells([1, 3, 2, 4, 6, 5])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(as_bells([1, 3, 2, 4, 5, 6]), new_row)

    def test_dixons_two_leading_handstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Backstroke previous
        previous_row = as_bells([2, 4, 1, 3, 5, 6])
        new_row = generator._gen_row(previous_row, is_handstroke=True, index=0)
        self.assertEqual(as_bells([4, 2, 3, 1, 6, 5]), new_row)

    def test_dixons_two_leading_backstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Handstroke previous
        previous_row = as_bells([2, 4, 1, 3, 6, 5])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(as_bells([2, 1, 4, 3, 5, 6]), new_row)

    def test_dixons_five_leading_handstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Handstroke previous
        previous_row = as_bells([5, 3, 6, 1, 4, 2])
        new_row = generator._gen_row(previous_row, is_handstroke=True, index=0)
        self.assertEqual(as_bells([3, 5, 1, 6, 2, 4]), new_row)

    def test_dixons_five_leading_backstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Handstroke previous
        previous_row = as_bells([5, 6, 3, 4, 1, 2])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(as_bells([5, 3, 6, 1, 4, 2]), new_row)
