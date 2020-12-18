""" A module containing a type that encapsulates a stroke. """

from typing import Any


class Stroke:
    """ A new-type of 'bool' that encapsulates a stroke: i.e. HANDSTROKE or BACKSTROKE. """

    def __init__(self, is_handstroke: bool) -> None:
        self._is_handstroke = is_handstroke

    def is_hand(self) -> bool:
        """ Returns true if this Stroke represents a handstroke.
        Equivalent to `stroke == HANDSTROKE`.
        """
        return self._is_handstroke

    def is_back(self) -> bool:
        """ Returns true if this Stroke represents a backstroke.
        Equivalent to `stroke == BACKSTROKE`.
        """
        return not self._is_handstroke

    @classmethod
    def from_index(cls, index: int) -> 'Stroke':
        """ Returns the stroke of the row that would exist at a given index. """
        return cls(index % 2 == 0)

    def opposite(self) -> 'Stroke':
        """ Returns the opposite Stroke to the current one. """
        return Stroke(not self._is_handstroke)

    def char(self) -> str:
        """ Returns a single-character string of 'H' or 'B'. """
        return "H" if self._is_handstroke else "B"

    def __str__(self) -> str:
        return "HANDSTROKE" if self._is_handstroke else "BACKSTROKE"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Stroke):
            return other._is_handstroke == self._is_handstroke
        return False

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __inverse__(self) -> 'Stroke':
        return self.opposite()

    def __hash__(self) -> int:
        return self._is_handstroke.__hash__()


HANDSTROKE: Stroke = Stroke(True)
BACKSTROKE: Stroke = Stroke(False)
