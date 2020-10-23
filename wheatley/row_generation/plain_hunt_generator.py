""" A module to hold a row generator that produces plain hunt on any (even) stage. """

from wheatley.aliases import Places, Row
from wheatley.stroke import Stroke

from .row_generator import RowGenerator


class PlainHuntGenerator(RowGenerator):
    """ A row generator to create plain hunt on any stage. """

    def summary_string(self) -> str:
        """ Returns a short string summarising the RowGenerator. """
        return f"Plain Hunt on {self.stage}"

    def _gen_row(self, previous_row: Row, stroke: Stroke, index: int) -> Row:
        if stroke.is_hand():
            return self.permute(previous_row, Places([]))
        return self.permute(previous_row, Places([1, self.stage]))
