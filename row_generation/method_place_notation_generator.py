""" Module to hold a RowGenerator to generate rows from a method title. """

import xml.etree.ElementTree as ET

import requests

from .place_notation_generator import PlaceNotationGenerator


class MethodPlaceNotationGenerator(PlaceNotationGenerator):
    """ A class to generate rows given a method title. """

    def __init__(self, method_title: str):
        method_xml = self._fetch_method(method_title)
        method_pn, stage = self._parse_xml(method_xml)
        super(MethodPlaceNotationGenerator, self).__init__(stage, method_pn)

    @staticmethod
    def _parse_xml(method_xml: str):
        method_parsed_xml = ET.fromstring(method_xml)
        xmlns = '{http://methods.ringing.org/NS/method}'

        # Schema at http://methods.ringing.org/xml.html
        symblock = method_parsed_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'symblock')
        block = method_parsed_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'block')
        stage = int(method_parsed_xml.find(xmlns + 'method/' + xmlns + 'stage').text)

        if len(symblock) != 0:
            notation = symblock[0].text
            lead_end = symblock[1].text
            return f"&{notation},&{lead_end}", stage
        elif len(block) != 0:
            notation = block[0].text
            return notation, stage
        else:
            raise Exception("Place notation not found")

    @staticmethod
    def _fetch_method(method_title):
        params = {'title': method_title, 'fields': 'pn|stage'}
        source = requests.get('http://methods.ringing.org/cgi-bin/simple.pl', params=params)
        source.raise_for_status()
        return source.text
