""" A module to hold the row generator that generates rows given some place notations. """

from typing import List, Dict

from wheatley.bell import Bell

from .helpers import convert_pn, convert_to_bell_string
from .row_generator import RowGenerator


class PlaceNotationGenerator(RowGenerator):
    """ A row generator to generate rows given a place notation. """

    # Dict Lead Index: String PlaceNotation
    # 0 for end of the lead
    DefaultBob = {0: '14'}
    DefaultSingle = {0: '1234'}

    def __init__(self, stage: int, method: str, bob: Dict[int, str] = None,
                 single: Dict[int, str] = None):
        super().__init__(stage)

        if bob is None:
            bob = PlaceNotationGenerator.DefaultBob
        if single is None:
            single = PlaceNotationGenerator.DefaultSingle

        self.method_pn = convert_pn(method)
        self.lead_len = len(self.method_pn)

        def parse_call_dict(unparsed_calls):
            """ Parse a dict of type `int => str` to `int => [PlaceNotation]`. """
            parsed_calls = {}

            for i, place_notation_str in unparsed_calls.items():
                # Parse the place notation string into a list of place notations, adjust the
                # call locations by the length of their calls (so that e.g. `0` always refers to
                # the lead end regardless of how long the calls are).
                converted_place_notations = convert_pn(place_notation_str)

                # Add the processed call to the output dictionary
                parsed_calls[(i - 1) % self.lead_len] = converted_place_notations

            return parsed_calls

        self.bobs_pn = parse_call_dict(bob)
        self.singles_pn = parse_call_dict(single)

        self._generating_call_pn: List[List[int]] = []

    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        lead_index = index % self.lead_len

        if self._has_bob and self.bobs_pn.get(lead_index):
            self._generating_call_pn = list(self.bobs_pn[lead_index])
            self.logger.info(f"Bob at index {lead_index}")
            self.reset_calls()
        elif self._has_single and self.singles_pn.get(lead_index):
            self._generating_call_pn = list(self.singles_pn[lead_index])
            self.logger.info(f"Single at index {lead_index}")
            self.reset_calls()

        if self._generating_call_pn:
            place_notation = self._generating_call_pn.pop(0)
        else:
            place_notation = self.method_pn[lead_index]

        return self.permute(previous_row, place_notation)

    @staticmethod
    def grandsire(stage: int):
        """ Generates Grandsire on a given stage. """
        stage_bell = convert_to_bell_string(stage)

        cross_notation = stage_bell if stage % 2 else '-'

        main_body = ["1" if i % 2 else cross_notation for i in range(2 * stage)]
        main_body[0] = "3"
        notation = ".".join(main_body)

        return PlaceNotationGenerator(stage, notation, bob={-1: "3"}, single={-1: "3.123"})

    @staticmethod
    def stedman(stage: int):
        """ Generates Stedman on a given stage (even bell Stedman will cause an exception). """
        assert stage % 2 == 1

        if stage == 5:
            return PlaceNotationGenerator.stedman_doubles()

        stage_bell = convert_to_bell_string(stage)
        stage_bell_1 = convert_to_bell_string(stage - 1)
        stage_bell_2 = convert_to_bell_string(stage - 2)

        notation = f"3.1.{stage_bell}.3.1.3.1.3.{stage_bell}.1.3.1"

        return PlaceNotationGenerator(stage, notation, bob={3: stage_bell_2, 9: stage_bell_2},
                                      single={3: f"{stage_bell_2}{stage_bell_1}{stage_bell}",
                                              9: f"{stage_bell_2}{stage_bell_1}{stage_bell}"})

    @staticmethod
    def stedman_doubles():
        """ Generates Stedman on a given stage (even bell Stedman will cause an exception). """
        notation = "3.1.5.3.1.3.1.3.5.1.3.1"

        return PlaceNotationGenerator(5, notation, bob={}, single={6: "345", 12: "145"})
