""" A module to hold a row generator that produces plain hunt on any (even) stage. """

from typing import List

from wheatley.bell import Bell

from .row_generator import RowGenerator


class PlainHuntGenerator(RowGenerator):
    """ A row generator to create plain hunt on any (even) stage. """

    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        if is_handstroke:
            return self.permute(previous_row, [])

        return self.permute(previous_row, [1, self.stage])
