""" Helper functions for the row generation module. """

from typing import List

import itertools
import re

from wheatley.aliases import Places, Row
from wheatley.bell import Bell, BELL_NAMES

_CROSS_PN: Places = Places([])

STAGES = {
    "singles": 3,
    "minimus": 4,
    "doubles": 5,
    "minor": 6,
    "triples": 7,
    "major": 8,
    "caters": 9,
    "royal": 10,
    "cinques": 11,
    "maximus": 12,
    "sextuples": 13,
    "fourteen": 14,
    "septuples": 15,
    "sixteen": 16,
}


def convert_pn(pn_str: str, expect_symmetric: bool=False) -> List[Places]:
    """ Convert a place notation string into a list of places. """
    if "," in pn_str:
        return list(itertools.chain.from_iterable(convert_pn(part, True) for part in pn_str.split(",")))

    if expect_symmetric:
        symmetric = not pn_str.startswith('+')
    else:
        symmetric = pn_str.startswith('&')

    # Assumes a valid place notation string is delimited by `.`
    # These can optionally be omitted around an `-` or `x`
    # We substitute to ensure `-` is surrounded by `.` and replace any `..` caused by `--` => `.-..-.
    dot_delimited_string = re.sub("[.]*[x-][.]*", ".-.", pn_str).strip('.&+ ')
    deduplicated_string = dot_delimited_string.replace('..', '.').split('.')

    # We suppress the type error here, because mypy will assign the list comprehension type 'List[object]',
    # not 'List[Places]'.
    converted: List[Places] = [[convert_bell_string(y) for y in place] # type: ignore
                 if place != '-' else _CROSS_PN
                 for place in deduplicated_string]

    if symmetric:
        return converted + list(reversed(converted[:-1]))
    return converted


def convert_bell_string(bell: str) -> int:
    """ Convert a single-char string representing a bell into an integer. """
    try:
        return BELL_NAMES.index(bell) + 1
    except ValueError as e:
        raise ValueError(f"'{bell}' is not known bell symbol") from e


def convert_to_bell_string(bell: int) -> str:
    """ Convert an integer into the equivalent bell name. """
    if bell <= 0 or bell >= len(BELL_NAMES) + 1:
        raise ValueError(f"'{bell}' is not known bell number")

    return BELL_NAMES[bell - 1]


def rounds(number_of_bells: int) -> Row:
    """ Generate rounds on the given number of bells. """
    return Row([Bell.from_number(i) for i in range(1, number_of_bells + 1)])
