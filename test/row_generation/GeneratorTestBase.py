from unittest.case import TestCase


class GeneratorTestBase(TestCase):
    @staticmethod
    def rounds(stage: int):
        number_of_bells = stage + 1 if stage % 2 else stage
        return [i for i in range(1, number_of_bells + 1)]

    @staticmethod
    def gen_rows(generator, count, start_at_hand=True):
        return list(GeneratorTestBase.yield_rows(generator, count, start_at_hand))

    @staticmethod
    def yield_rows(generator, count, start_at_hand=True):
        is_handstroke = start_at_hand
        for _ in range(count):
            yield [bell.number for bell in generator.next_row(is_handstroke)]
            is_handstroke = not is_handstroke
