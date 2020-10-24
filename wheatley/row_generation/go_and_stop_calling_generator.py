""" A module to hold a decorator class to add calling go and stop to a RowGenerator. """

# pylint: disable=protected-access

from typing import List, Tuple

from wheatley import calls
from wheatley.aliases import Row
from wheatley.stroke import Stroke

from .row_generator import RowGenerator


class GoAndStopCallingGenerator(RowGenerator):
    """ A decorator to add calling go and stop to an existing RowGenerator. """

    def __init__(self, generator: RowGenerator) -> None:
        super().__init__(generator.stage)

        self.generator = generator
        self.called_go = False

    def summary_string(self) -> str:
        """ Returns a short string summarising the RowGenerator. """
        return f"{self.generator.summary_string}, calling 'Go' and 'Stop'"

    def _gen_row_and_call(self, previous_row: Row, stroke: Stroke, index: int) -> Tuple[Row, List[str]]:
        (next_row, next_calls) = self.generator._gen_row_and_call(previous_row, stroke, index)
        # Add `That's All` if the touch is about to come round
        return (next_row, [calls.THATS_ALL] + next_calls)

    def _gen_row(self, previous_row: Row, stroke: Stroke, index: int) -> Row:
        raise NotImplementedError()
