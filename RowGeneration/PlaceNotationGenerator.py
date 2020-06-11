from typing import List, Dict, Union, Tuple

from RowGeneration.Helpers import convert_pn, convert_to_bell_string
from RowGeneration.RowGenerator import RowGenerator


class PlaceNotationGenerator(RowGenerator):
    DefaultBob = {-1: '14'}
    DefaultSingle = {-1: '1234'}

    def __init__(self, stage: int, method: str, bob: Dict[int, str] = None, single: Dict[int, str] = None,
                 auto_start=True):
        super(PlaceNotationGenerator, self).__init__(stage, auto_start)
        if bob is None:
            bob = PlaceNotationGenerator.DefaultBob
        if single is None:
            single = PlaceNotationGenerator.DefaultSingle

        self.method_pn = convert_pn(method)
        self.lead_len = len(self.method_pn)

        self.bobs_pn = {i % self.lead_len: convert_pn(pn) for i, pn in bob.items()}
        self.singles_pn = {i % self.lead_len: convert_pn(pn) for i, pn in single.items()}

        self._generating_call_pn: List[List[int]] = []

    def _gen_row(self, previous_row: List[int], is_handstroke: bool, index: int) -> List[int]:
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
        assert stage % 2

        stage_bell = convert_to_bell_string(stage)

        main_body = [stage_bell if i % 2 else "1" for i in range(1, 2 * stage + 1)]
        main_body[0] = "3"
        notation = ".".join(main_body)
        return PlaceNotationGenerator(stage, notation, bob={-2: "3"}, single={-2: "3.123"})

    @staticmethod
    def stedman(stage: int):
        assert stage % 2

        if stage == 5:
            return PlaceNotationGenerator.stedman_doubles()

        stage_bell = convert_to_bell_string(stage)
        stage_bell_1 = convert_to_bell_string(stage - 1)
        stage_bell_2 = convert_to_bell_string(stage - 2)

        notation = f"3.1.{stage_bell}.3.1.3.1.3.{stage_bell}.1.3.1"
        return PlaceNotationGenerator(stage, notation, bob={2: stage_bell_2, 8: stage_bell_2},
                                      single={2: f"{stage_bell_2}{stage_bell_1}{stage_bell}",
                                              8: f"{stage_bell_2}{stage_bell_1}{stage_bell}"})

    @staticmethod
    def stedman_doubles():
        notation = "3.1.5.3.1.3.1.3.5.1.3.1"
        return PlaceNotationGenerator(5, notation, bob={}, single={5: "345", 11: "145"})
