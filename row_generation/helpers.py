from typing import List

import itertools
import re

_CROSS_PN = []
_LOOKUP_NAME = "!1234567890ET"


def convert_pn(pn_str: str) -> List[List[int]]:
    if "," in pn_str:
        return list(itertools.chain.from_iterable(convert_pn(part) for part in pn_str.split(",")))

    symmetric = pn_str.startswith('&')

    cleaned = re.sub("[.]*[x-][.]*", ".-.", pn_str).strip('.& ').split('.')

    converted = [[convert_bell_string(y) for y in place] if place != '-' else _CROSS_PN
                 for place in cleaned]
    if symmetric:
        return converted + list(reversed(converted[:-1]))

    return converted


def convert_bell_string(bell: str) -> int:
    try:
        return _LOOKUP_NAME.index(bell)
    except ValueError:
        raise ValueError(f"'{bell}' is not known bell symbol")


def convert_to_bell_string(bell: int) -> str:
    if bell <= 0 or bell >= len(_LOOKUP_NAME):
        raise ValueError(f"'{bell}' is not known bell number")
    return _LOOKUP_NAME[bell]
