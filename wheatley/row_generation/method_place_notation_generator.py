""" Module to hold a RowGenerator to generate rows from a method title. """

import xml.etree.ElementTree as ET
from typing import Optional, Tuple

import requests

from wheatley.aliases import CallDef

from .dixonoids_generator import DixonoidsGenerator
from .helpers import STAGES
from .plain_hunt_generator import PlainHuntGenerator
from .place_notation_generator import PlaceNotationGenerator
from .row_generator import RowGenerator


def generator_from_special_title(method_title: str) -> Optional[RowGenerator]:
    """ Creates a row generator from special method titles. """
    lowered_title = method_title.lower().strip()
    if " " not in lowered_title:
        raise MethodNotFoundError(method_title)

    method_name, stage_name = lowered_title.rsplit(" ", 1)
    method_name = method_name.strip()

    if stage_name.isdigit() and int(stage_name) in STAGES.values():
        stage = int(stage_name)
    elif stage_name in STAGES:
        stage = STAGES[stage_name]
    else:
        raise MethodNotFoundError(method_title)

    if method_name == "grandsire" and stage >= 5:
        return PlaceNotationGenerator.grandsire(stage)
    if method_name == "stedman" and stage % 2 and stage >= 5:
        return PlaceNotationGenerator.stedman(stage)
    if method_name in ["plain hunt", "plain hunt on"]:
        return PlainHuntGenerator(stage)
    if method_name == "dixon's bob" and stage == 6:
        return DixonoidsGenerator(stage)
    return None


class MethodNotFoundError(ValueError):
    """
    An error class to store the error thrown when a method title is inputted that doesn't have an
    entry in the CC method library.
    """

    def __init__(self, name: str) -> None:
        super().__init__()

        self._name = name

    def __str__(self) -> str:
        return f"No method with title '{self._name}' found."


class MethodPlaceNotationGenerator(PlaceNotationGenerator):
    """ A class to generate rows given a method title. """

    def __init__(self, method_title: str, bob: CallDef, single: CallDef, start_row: int = 0) -> None:
        method_xml = self._fetch_method(method_title)

        try:
            method_pn, stage, actual_title = self._parse_xml(method_xml)
            self._title = actual_title
        except AttributeError as e:
            raise MethodNotFoundError(method_title) from e

        super().__init__(
            stage,
            method_pn,
            bob,
            single,
            start_row
        )

    def summary_string(self) -> str:
        """ Returns a short string summarising the RowGenerator. """
        return f"{self._title}"

    @staticmethod
    def _parse_xml(method_xml: str) -> Tuple[str, int, str]:
        method_parsed_xml = ET.fromstring(method_xml)
        xmlns = '{http://methods.ringing.org/NS/method}'

        # Unpack the title
        title_elems = method_parsed_xml.findall(xmlns + 'method/' + xmlns + 'title')
        if len(title_elems) == 0:
            raise AttributeError("No method title found in XML")
        title: Optional[str] = title_elems[0].text
        assert title is not None

        # Schema at http://methods.ringing.org/xml.html
        symblock = method_parsed_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'symblock')
        block = method_parsed_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'block')
        # Unpack the stage piece-by-piece to appease the type checker and assert expected types at runtime
        maybe_stage_str = method_parsed_xml.find(xmlns + 'method/' + xmlns + 'stage')
        assert maybe_stage_str is not None
        stage_str = maybe_stage_str.text
        assert isinstance(stage_str, str)
        stage = int(stage_str)

        if len(symblock) != 0:
            notation = symblock[0].text
            lead_end = symblock[1].text
            return f"&{notation},&{lead_end}", stage, title

        if len(block) != 0:
            notation = block[0].text
            assert notation is not None
            return notation, stage, title

        raise Exception("Place notation not found")

    @staticmethod
    def _fetch_method(method_title: str) -> str:
        params = {'title': method_title, 'fields': 'title|pn|stage'}
        source = requests.get('http://methods.ringing.org/cgi-bin/simple.pl', params=params)
        source.raise_for_status()

        return source.text
