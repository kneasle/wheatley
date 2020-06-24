from typing import List

from bell import Bell
from row_generation import DixonoidsGenerator
from test.row_generation import GeneratorTestBase


class DixonoidsGeneratorTests(GeneratorTestBase):
    @staticmethod
    def _row(nums: List[int]) -> List[Bell]:
        return [Bell.from_number(x) for x in nums]

    def test_dixons_treble_leading_handstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Backstroke previous
        previous_row = self._row([1, 4, 3, 2, 5, 6])
        new_row = generator._gen_row(previous_row, is_handstroke=True, index=0)
        self.assertEqual(self._row([4, 1, 2, 3, 6, 5]), new_row)

    def test_dixons_treble_leading_backstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Handstroke previous
        previous_row = self._row([1, 3, 2, 4, 6, 5])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(self._row([1, 3, 4, 2, 5, 6]), new_row)

    def test_dixons_treble_leading_backstroke_bob(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        generator.set_bob()
        # Handstroke previous
        previous_row = self._row([1, 3, 2, 4, 6, 5])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(self._row([1, 2, 3, 4, 5, 6]), new_row)

    def test_dixons_treble_leading_backstroke_single(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        generator.set_single()
        # Handstroke previous
        previous_row = self._row([1, 3, 2, 4, 6, 5])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(self._row([1, 3, 2, 4, 5, 6]), new_row)

    def test_dixons_two_leading_handstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Backstroke previous
        previous_row = self._row([2, 4, 1, 3, 5, 6])
        new_row = generator._gen_row(previous_row, is_handstroke=True, index=0)
        self.assertEqual(self._row([4, 2, 3, 1, 6, 5]), new_row)

    def test_dixons_two_leading_backstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Handstroke previous
        previous_row = self._row([2, 4, 1, 3, 6, 5])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(self._row([2, 1, 4, 3, 5, 6]), new_row)

    def test_dixons_five_leading_handstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Handstroke previous
        previous_row = self._row([5, 3, 6, 1, 4, 2])
        new_row = generator._gen_row(previous_row, is_handstroke=True, index=0)
        self.assertEqual(self._row([3, 5, 1, 6, 2, 4]), new_row)

    def test_dixons_five_leading_backstroke(self):
        generator = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
        # Handstroke previous
        previous_row = self._row([5, 6, 3, 4, 1, 2])
        new_row = generator._gen_row(previous_row, is_handstroke=False, index=0)
        self.assertEqual(self._row([5, 3, 6, 1, 4, 2]), new_row)
