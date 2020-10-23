"""
A module to hold a place-holder row generator that accepts all tower sizes but throws an exception instead of
producing rows.
"""

from wheatley.aliases import Row
from wheatley.stroke import Stroke

from .row_generator import RowGenerator


class NullRowGenError(Exception):
    """ An exception thrown when a row is requested from a 'NullGenerator'. """

    def __str__(self) -> str:
        return "_gen_row() called on a PlaceHolderGenerator"


class PlaceHolderGenerator(RowGenerator):
    """
    A place holder row generator that accepts any tower size but throws an exception when rows are requested.
    """

    def __init__(self) -> None:
        # Make the stage 0
        super().__init__(0)

    def summary_string(self) -> str:
        """ Returns a short string summarising the RowGenerator. """
        return "nothing"

    def _gen_row(self, previous_row: Row, stroke: Stroke, index: int) -> Row:
        raise NullRowGenError()
