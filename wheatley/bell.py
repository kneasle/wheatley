"""
A module to contain a Bell class used to encapsulate the idea of a Bell and remove off-by-one
errors related to deciding whether the treble is bell #0 or bell #1.
"""

from typing import Any


BELL_NAMES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "E", "T", "A", "B", "C", "D"]
MAX_BELL = len(BELL_NAMES)


class Bell:
    """ A class to encapsulate the idea of a bell. """

    @classmethod
    def from_str(cls, bell_str: str) -> 'Bell':
        """
        Generates a Bell object from a string representing that bell's name.
        This works according to the standard convention, so Bell.from_str('1') will represent
        the treble, and Bell.from_str('T') will represent the twelfth.
        """
        try:
            index = BELL_NAMES.index(bell_str)
        except ValueError as e:
            raise ValueError(f"'{bell_str}' is not known bell symbol") from e

        return cls(index)

    @classmethod
    def from_number(cls, bell_num: int) -> 'Bell':
        """
        Generates a Bell from a 1-indexed number, so Bell.from_number(1) will return a Bell
        representing the treble.
        """
        return cls(bell_num - 1)

    @classmethod
    def from_index(cls, bell_index: int) -> 'Bell':
        """
        Generates a Bell from a 0-indexed number, so Bell.from_number(0) will return a Bell
        representing the treble.
        """
        return cls(bell_index)

    def __init__(self, index: int) -> None:
        """
        Constructs a Bell from a given 0-indexed index.  Should not be used outside this class -
        see `Bell.from_index` and `Bell.from_number` instead.
        """
        if index < 0 or index >= len(BELL_NAMES):
            raise ValueError(f"'{index}' is not known bell index")

        self.index = index

    @property
    def number(self) -> int:
        """ Gets the 1-indexed number representing this bell. """
        return self.index + 1

    def __str__(self) -> str:
        """ Converts this bell to a single-character string representing this bell. """
        return BELL_NAMES[self.index]

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:
        """ Determines if two Bells are equal. """
        return isinstance(other, Bell) and other.index == self.index

    def __hash__(self) -> int:
        """ Generates a has of a Bell. """
        return self.index
