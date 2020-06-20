import unittest

from RowGeneration.PlainHuntGenerator import PlainHuntGenerator
from test.GeneratorTestBase import GeneratorTestBase


class PlainHuntGeneratorTests(GeneratorTestBase):

    def test_auto_start_rounds_twice(self):
        stage = 4
        rounds = self.rounds(stage)

        generator = PlainHuntGenerator(stage, auto_start=True)

        self.assertEqual(generator.next_row(True), rounds)
        self.assertEqual(generator.next_row(False), rounds)

        self.assertNotEqual(generator.next_row(True), rounds)

    def test_not_auto_start_keeps_rounds(self):
        stage = 4
        rounds = self.rounds(stage)

        generator = PlainHuntGenerator(stage, auto_start=False)

        with self.assertLogs() as test_logging:
            for row in self.yield_rows(generator, 10):
                self.assertEqual(row, rounds)
            self.assertEqual(test_logging.output, ["INFO:ROWGEN:Rounds" for _ in range(10)])

    def test_not_auto_start_rounds_until_go(self):
        stage = 4
        rounds = self.rounds(stage)

        generator = PlainHuntGenerator(stage, auto_start=False)

        for row in self.yield_rows(generator, 4):
            self.assertEqual(row, rounds)

        generator.set_go()

        self.assertNotEqual(generator.next_row(True), rounds)

    def test_not_auto_start_rounds_until_go_waits_for_handstroke(self):
        stage = 4
        rounds = self.rounds(stage)

        generator = PlainHuntGenerator(stage, auto_start=False)

        for row in self.yield_rows(generator, 5):
            self.assertEqual(row, rounds)

        generator.set_go()

        self.assertEqual(generator.next_row(False), rounds)
        self.assertNotEqual(generator.next_row(True), rounds)

    def test_singles(self):
        stage = 3
        generator = PlainHuntGenerator(stage, auto_start=True)

        self.initial_rounds(generator, stage)
        rows = self.gen_rows(generator, 6)
        self.assertEqual([[2, 1, 3, 4],
                          [2, 3, 1, 4],
                          [3, 2, 1, 4],
                          [3, 1, 2, 4],
                          [1, 3, 2, 4],
                          [1, 2, 3, 4]],
                         rows)

    def test_reset_no_auto_starts(self):
        stage = 3
        rounds = self.rounds(stage)
        generator = PlainHuntGenerator(stage, auto_start=False)
        generator.set_go()

        self.initial_rounds(generator, stage)
        initial_rows = self.gen_rows(generator, 3)
        self.assertEqual([[2, 1, 3, 4],
                          [2, 3, 1, 4],
                          [3, 2, 1, 4]],
                         initial_rows)
        generator.reset()
        rounds_rows = self.gen_rows(generator, 3, start_at_hand=False)
        self.assertEqual([rounds, rounds, rounds],
                         rounds_rows)

        generator.set_go()
        # Starts from beginning again
        second_rows = self.gen_rows(generator, 3)
        self.assertEqual([[2, 1, 3, 4],
                          [2, 3, 1, 4],
                          [3, 2, 1, 4]],
                         second_rows)

    def test_reset_auto_starts_backstroke(self):
        stage = 3
        rounds = self.rounds(stage)
        generator = PlainHuntGenerator(stage, auto_start=True)

        self.initial_rounds(generator, stage)
        initial_rows = self.gen_rows(generator, 3)
        self.assertEqual([[2, 1, 3, 4],
                          [2, 3, 1, 4],
                          [3, 2, 1, 4]],
                         initial_rows)
        generator.reset()
        # Rounds then goes again
        second_rows = self.gen_rows(generator, 3, start_at_hand=False)
        self.assertEqual([rounds, [2, 1, 3, 4], [2, 3, 1, 4]],
                         second_rows)

    def test_reset_auto_starts_handstroke(self):
        stage = 3
        rounds = self.rounds(stage)
        generator = PlainHuntGenerator(stage, auto_start=True)

        self.initial_rounds(generator, stage)
        initial_rows = self.gen_rows(generator, 4)
        self.assertEqual([[2, 1, 3, 4],
                          [2, 3, 1, 4],
                          [3, 2, 1, 4],
                          [3, 1, 2, 4]],
                         initial_rows)
        generator.reset()
        # Rounds then goes again
        second_rows = self.gen_rows(generator, 4, start_at_hand=True)
        self.assertEqual([rounds, rounds, [2, 1, 3, 4], [2, 3, 1, 4]],
                         second_rows)

    def test_minimus(self):
        stage = 4
        generator = PlainHuntGenerator(stage, auto_start=True)

        self.initial_rounds(generator, stage)
        rows = self.gen_rows(generator, 8)
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
        generator = PlainHuntGenerator(stage, auto_start=True)

        self.initial_rounds(generator, stage)
        rows = self.gen_rows(generator, 3)
        self.assertEqual([[2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 11, 12],
                          [2, 4, 1, 6, 3, 8, 5, 10, 7, 11, 9, 12],
                          [4, 2, 6, 1, 8, 3, 10, 5, 11, 7, 9, 12]],
                         rows)

    def test_maximus(self):
        stage = 12
        generator = PlainHuntGenerator(stage, auto_start=True)

        self.initial_rounds(generator, stage)
        rows = self.gen_rows(generator, 3)
        self.assertEqual([[2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11],
                          [2, 4, 1, 6, 3, 8, 5, 10, 7, 12, 9, 11],
                          [4, 2, 6, 1, 8, 3, 10, 5, 12, 7, 11, 9]],
                         rows)


if __name__ == '__main__':
    unittest.main()
