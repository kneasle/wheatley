""" Helper functions for the row generation module. """

from typing import List

import itertools
import re

_CROSS_PN = []
_LOOKUP_NAME = "!1234567890ET"

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
    "maximus": 12
}


def convert_pn(pn_str: str) -> List[List[int]]:
    """ Convert a place notation string into a list of places. """
    if "," in pn_str:
        return list(itertools.chain.from_iterable(convert_pn(part) for part in pn_str.split(",")))

    symmetric = pn_str.startswith('&')

    # Assumes a valid place notation string is delimited by `.`
    # These can optionally be ommitted around an `-` or `x`
    # We substitute to ensure `-` is surrounded by `.` and replace any `..` caused by `--` => `.-..-.
    dot_delimited_string = re.sub("[.]*[x-][.]*", ".-.", pn_str).strip('.& ')
    deduplicated_string = dot_delimited_string.replace('..', '.').split('.')

    converted = [[convert_bell_string(y) for y in place] if place != '-' else _CROSS_PN
                 for place in deduplicated_string]

    if symmetric:
        return converted + list(reversed(converted[:-1]))

    return converted


def convert_bell_string(bell: str) -> int:
    """ Convert a single-char string representing a bell into an integer. """
    try:
        return _LOOKUP_NAME.index(bell)
    except ValueError as e:
        raise ValueError(f"'{bell}' is not known bell symbol") from e


def convert_to_bell_string(bell: int) -> str:
    """ Convert an integer into the equivalent bell name. """
    if bell <= 0 or bell >= len(_LOOKUP_NAME):
        raise ValueError(f"'{bell}' is not known bell number")

    return _LOOKUP_NAME[bell]
