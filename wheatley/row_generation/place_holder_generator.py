"""
A module to hold a place-holder row generator that accepts all tower sizes but throws an exception instead of
producing rows.
"""

from typing import List

from wheatley.bell import Bell

from .row_generator import RowGenerator


class NullRowGenError(Exception):
    """ An exception thrown when a row is requested from a 'NullGenerator'. """

    def __str__(self):
        return "_gen_row() called on a PlaceHolderGenerator"


class PlaceHolderGenerator(RowGenerator):
    """
    A place holder row generator that accepts any tower size but throws an exception when rows are requested.
    """

    def __init__(self):
        # Make the stage 0
        super().__init__(0)

    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        raise NullRowGenError()

    # Override as warnings make no sense from this place holder
    def set_tower_size(self, tower_size):
        pass
