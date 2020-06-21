from random import random
from typing import List

from Calls import Calls
from RowGeneration.RowGenerator import RowGenerator
from bell import Bell
from tower import RingingRoomTower


class GoAndStopCallingGenerator(RowGenerator):

    def __init__(self, generator: RowGenerator, tower: RingingRoomTower):
        super().__init__(generator.stage)
        self.tower = tower
        self.generator = generator
        self.called_go = False

    def next_row(self, is_handstroke: bool):
        if not self.called_go and not is_handstroke and random.choices([True, False], [1, 3]):
            self.tower.make_call(Calls.Go)
        return super(GoAndStopCallingGenerator, self).next_row(is_handstroke)

    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        next_row = self.generator._gen_row(previous_row, is_handstroke, index)
        if next_row == self.rounds():
            self.tower.make_call(Calls.ThatsAll)

        return next_row
