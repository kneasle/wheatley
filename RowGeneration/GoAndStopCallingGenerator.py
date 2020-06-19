from random import random
from typing import List

from Calls import Calls
from RowGeneration.RowGenerator import RowGenerator
from tower import RingingRoomTower


class GoAndStopCallingGenerator(RowGenerator):

    def __init__(self, generator: RowGenerator, tower: RingingRoomTower):
        super().__init__(generator.stage)
        self.tower = tower
        self.generator = generator

    def next_row(self, is_handstroke: bool):
        if self._index == -1 and self.auto_start:
            self.tower.make_call(Calls.Go)
        if not self.auto_start and not self._has_go and not is_handstroke and random.choices([True, False], [1, 3]):
            self.tower.make_call(Calls.Go)
        return super(GoAndStopCallingGenerator, self).next_row(is_handstroke)

    def _gen_row(self, previous_row: List[int], is_handstroke: bool, index: int) -> List[int]:
        next_row = self.generator._gen_row(previous_row, is_handstroke, index)
        if next_row == self.rounds():
            self.tower.make_call(Calls.ThatsAll)

        return next_row
