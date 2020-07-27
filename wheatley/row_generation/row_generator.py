""" A module to contain the abstract base class that all row generators inherit from. """

import logging
from abc import ABCMeta, abstractmethod
from typing import List

from wheatley.bell import Bell


class RowGenerator(metaclass=ABCMeta):
    """ Abstract base class for behaviours common to all row generators. """

    logger_name = "ROWGEN"

    def __init__(self, stage: int):
        self.stage = stage
        self.logger = logging.getLogger(self.logger_name)

        # Ensure there is a cover bell
        self.number_of_bells = self.stage + 1 if self.stage % 2 else self.stage

        self._has_bob = False
        self._has_single = False
        self._index = 0
        self._row = self.rounds()

    def reset(self):
        """ Reset the row generator. """

        self.logger.info("Reset")
        self._has_bob = False
        self._has_single = False
        self._index = 0
        self._row = self.rounds()

    def reset_calls(self):
        """ Clear the pending call flags. """

        self.logger.info("Reset calls")
        self._has_bob = False
        self._has_single = False

    def next_row(self, is_handstroke: bool) -> List[Bell]:
        """ Generate the next row, and mutate state accordingly. """

        self._row = self._gen_row(self._row, is_handstroke, self._index)
        self._add_cover_if_required()

        self._index += 1

        message = " ".join([str(bell) for bell in self._row])
        self.logger.info(message)

        return self._row

    def set_bob(self):
        """ Set the flag that a bob has been made. """

        self._has_bob = True

    def set_single(self):
        """ Set the flag that a single has been made. """

        self._has_single = True

    def rounds(self) -> List[Bell]:
        """ Generate rounds of the stage given by this RowGenerator. """

        return [Bell.from_number(i) for i in range(1, self.number_of_bells + 1)]

    def _add_cover_if_required(self):
        if len(self._row) == self.number_of_bells - 1:
            self._row.append(Bell.from_number(self.number_of_bells))

    @abstractmethod
    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        pass

    def permute(self, row: List[Bell], places: List[int]) -> List[Bell]:
        """ Permute a row by a place notation given by `places`. """

        new_row = list(row)
        i = 1
        if places and places[0] % 2 == 0:
            # Skip 1 for implicit lead when lowest pn is even
            i += 1

        while i < self.stage:
            if i in places:
                i += 1
                continue
            else:
                # If not in place, must swap, index is 1 less than place
                new_row[i - 1], new_row[i] = new_row[i], new_row[i - 1]
                i += 2

        return new_row
