"""
A module to contain a Bell class used to encapsulate the idea of a Bell and remove off-by-one
errors related to deciding whether the treble is bell #0 or bell #1.
"""

class Bell:
    """ A class to encapsulate the idea of a bell. """

    @classmethod
    def from_str(cls, bell_str: str):
        """
        Generates a Bell object from a string representing that bell's name.
        This works according to the standard convention, so Bell.from_str('1') will represent
        the treble, and Bell.from_str('T') will represent the twelfth.
        """

        try:
            index = Bell._lookup_name.index(bell_str)
        except ValueError:
            raise ValueError(f"'{bell_str}' is not known bell symbol")
        return cls(index)

    @classmethod
    def from_number(cls, bell_num: int):
        """
        Generates a Bell from a 1-indexed number, so Bell.from_number(1) will return a Bell
        representing the treble.
        """

        return cls(bell_num - 1)

    @classmethod
    def from_index(cls, bell_index: int):
        """
        Generates a Bell from a 0-indexed number, so Bell.from_number(0) will return a Bell
        represeting the treble.
        """

        return cls(bell_index)

    def __init__(self, index: int):
        """
        Constructs a Bell from a given 0-indexed index.  Should not be used outside this class -
        see `Bell.from_index` and `Bell.from_number` instead.
        """

        if index < 0 or index >= len(self._lookup_name):
            raise ValueError(f"'{index}' is not known bell index")
        self.index = index

    @property
    def number(self):
        """ Gets the 1-indexed number representing this bell. """

        return self.index + 1

    _lookup_name = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "E", "T"]

    def __str__(self):
        """ Converts this bell to a single-character string representing this bell. """

        return self._lookup_name[self.index]

    def __eq__(self, other):
        """ Determines if two Bells are equal. """

        return isinstance(other, Bell) and other.index == self.index

    def __hash__(self):
        """ Generates a has of a Bell. """

        return self.index
