""" A module to hold the row generator that generates rows given some place notations. """

from typing import ClassVar, List, Dict

from wheatley.aliases import CallDef, Row, Places
from wheatley.stroke import Stroke

from .helpers import convert_pn, convert_to_bell_string
from .row_generator import RowGenerator


class PlaceNotationGenerator(RowGenerator):
    """ A row generator to generate rows given a place notation. """

    # Dict Lead Index: String PlaceNotation
    # 0 for end of the lead
    DefaultBob: ClassVar[CallDef] = CallDef({0: '14'})
    DefaultSingle: ClassVar[CallDef] = CallDef({0: '1234'})

    def __init__(self, stage: int, method: str, bob: CallDef = None, single: CallDef = None,
                 start_index: int = 0) -> None:
        super().__init__(stage)

        if bob is None:
            bob = PlaceNotationGenerator.DefaultBob
        if single is None:
            single = PlaceNotationGenerator.DefaultSingle

        self.method_pn = convert_pn(method)
        self.lead_len = len(self.method_pn)
        # Store the method place notation as a string for the summary string
        self.method_pn_string = method
        self.start_index = start_index

        def parse_call_dict(unparsed_calls: CallDef) -> Dict[int, List[Places]]:
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

        self._generating_call_pn: List[Places] = []

    def summary_string(self) -> str:
        """ Returns a short string summarising the RowGenerator. """
        return f"place notation '{self.method_pn_string}'"

    def _gen_row(self, previous_row: Row, stroke: Stroke, index: int) -> Row:
        assert self.lead_len > 0
        lead_index = (index + self.start_index) % self.lead_len

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

    def start_stroke(self) -> Stroke:
        return Stroke.from_index(self.start_index)

    @staticmethod
    def grandsire(stage: int) -> RowGenerator:
        """ Generates Grandsire on a given stage. """
        stage_bell = convert_to_bell_string(stage)

        cross_notation = stage_bell if stage % 2 else '-'

        main_body = ["1" if i % 2 else cross_notation for i in range(2 * stage)]
        main_body[0] = "3"
        notation = ".".join(main_body)

        return PlaceNotationGenerator(stage, notation, bob=CallDef({-1: "3"}), single=CallDef({-1: "3.123"}))

    @staticmethod
    def stedman(stage: int) -> RowGenerator:
        """ Generates Stedman on a given stage (even bell Stedman will cause an exception). """
        assert stage % 2 == 1

        if stage == 5:
            return PlaceNotationGenerator.stedman_doubles()

        stage_bell = convert_to_bell_string(stage)
        stage_bell_1 = convert_to_bell_string(stage - 1)
        stage_bell_2 = convert_to_bell_string(stage - 2)

        notation = f"3.1.{stage_bell}.3.1.3.1.3.{stage_bell}.1.3.1"

        return PlaceNotationGenerator(stage, notation, bob=CallDef({3: stage_bell_2, 9: stage_bell_2}),
                                      single=CallDef({3: f"{stage_bell_2}{stage_bell_1}{stage_bell}",
                                              9: f"{stage_bell_2}{stage_bell_1}{stage_bell}"}))

    @staticmethod
    def stedman_doubles() -> RowGenerator:
        """ Generates Stedman on a given stage (even bell Stedman will cause an exception). """
        notation = "3.1.5.3.1.3.1.3.5.1.3.1"

        return PlaceNotationGenerator(5, notation, bob=CallDef({}), single=CallDef({6: "345", 12: "145"}))
