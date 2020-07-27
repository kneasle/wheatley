""" Module to hold DixonoidsGenerator, a class for generating dixonoids. """

from typing import Dict, List

from wheatley.bell import Bell

from .helpers import convert_pn
from .row_generator import RowGenerator


class DixonoidsGenerator(RowGenerator):
    """ A class to generate rows of dixonoids. """

    DixonsRules = {
        0: ["x", "1"],
        1: ["x", "2"],
        2: ["x", "4"],
        4: ["x", "4"]
    }
    DefaultBob = {1: ["x", "4"]}
    DefaultSingle = {1: ["x", "1234"]}

    def __init__(self, stage: int, plain_rules: Dict[int, List[str]],
                 bob_rules: Dict[int, List[str]] = None, single_rules: Dict[int, List[str]] = None):
        """
        Initialises a dixonoid generator.

        :param plain_rules: Dictionary of leading bell: [handstroke pn, backstroke pn]
                            0: Matches any other bell
        :param bob_rules: Dictionary of leading bell: [handstroke pn, backstroke pn]
                          Only include bells which lead when a bob is rung
        :param single_rules: Dictionary of leading bell: [handstroke pn, backstroke pn]
                          Only include bells which lead when a single is rung
        """

        super(DixonoidsGenerator, self).__init__(stage)

        if bob_rules is None:
            bob_rules = self.DefaultBob
        if single_rules is None:
            single_rules = self.DefaultSingle

        self.plain_rules = self._convert_pn_dict(plain_rules)
        self.bob_rules = self._convert_pn_dict(bob_rules)
        self.single_rules = self._convert_pn_dict(single_rules)

    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        leading_bell = previous_row[0].number
        pn_index = 0 if is_handstroke else 1

        if self._has_bob and self.bob_rules.get(leading_bell):
            place_notation = self.bob_rules[leading_bell][pn_index]
            if not is_handstroke:
                self.reset_calls()
        elif self._has_single and self.single_rules.get(leading_bell):
            place_notation = self.single_rules[leading_bell][pn_index]
            if not is_handstroke:
                self.reset_calls()
        elif self.plain_rules.get(leading_bell):
            place_notation = self.plain_rules[leading_bell][pn_index]
        else:
            place_notation = self.plain_rules[0][pn_index]

        row = self.permute(previous_row, place_notation)
        return row

    @staticmethod
    def _convert_pn_dict(rules: Dict[int, List[str]]) -> Dict[int, List[List[int]]]:
        return {key: [convert_pn(pn)[0] for pn in places] for key, places in rules.items()}
