from typing import List, Iterator

from wheatley.bell import Bell


def rounds(stage: int) -> List[int]:
    number_of_bells = stage + 1 if stage % 2 else stage
    return [i for i in range(1, number_of_bells + 1)]


def as_bells(nums: List[int]) -> List[Bell]:
    return [Bell.from_number(x) for x in nums]


def gen_rows(generator, count, start_at_hand=True) -> List[int]:
    return list(yield_rows(generator, count, start_at_hand))


def yield_rows(generator, count, start_at_hand=True) -> Iterator[int]:
    is_handstroke = start_at_hand
    for _ in range(count):
        yield [bell.number for bell in generator.next_row(is_handstroke)]
        is_handstroke = not is_handstroke
