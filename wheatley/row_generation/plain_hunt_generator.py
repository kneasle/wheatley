""" A module to hold a row generator that produces plain hunt on any (even) stage. """

from wheatley.types import Row

from .row_generator import RowGenerator


class PlainHuntGenerator(RowGenerator):
    """ A row generator to create plain hunt on any stage. """

    def _gen_row(self, previous_row: Row, is_handstroke: bool, index: int) -> Row:
        if is_handstroke:
            return self.permute(previous_row, [])

        return self.permute(previous_row, [1, self.stage])
