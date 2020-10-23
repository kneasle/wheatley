""" A module to hold a decorator class to add calling go and stop to a RowGenerator. """

# pylint: disable=protected-access

import random

from wheatley import calls
from wheatley.aliases import Row
from wheatley.stroke import Stroke
from wheatley.tower import RingingRoomTower

from .row_generator import RowGenerator


class GoAndStopCallingGenerator(RowGenerator):
    """ A decorator to add calling go and stop to an existing RowGenerator. """

    def __init__(self, generator: RowGenerator, tower: RingingRoomTower) -> None:
        super().__init__(generator.stage)

        self.tower = tower
        self.generator = generator
        self.called_go = False

    def next_row(self, stroke: Stroke) -> Row:
        if not self.called_go and stroke.is_back() and random.choices([True, False], [1, 3]):
            self.tower.make_call(calls.GO)

        return super().next_row(stroke)

    def summary_string(self) -> str:
        """ Returns a short string summarising the RowGenerator. """
        return f"{self.generator.summary_string}, calling 'Go' and 'Stop'"

    def _gen_row(self, previous_row: Row, stroke: Stroke, index: int) -> Row:
        next_row = self.generator._gen_row(previous_row, stroke, index)

        if next_row == self.rounds():
            self.tower.make_call(calls.THATS_ALL)

        return next_row
