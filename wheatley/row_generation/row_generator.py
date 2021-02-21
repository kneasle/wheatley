""" A module to contain the abstract base class that all row generators inherit from. """

import logging
from typing import Dict, List, Tuple
from abc import ABCMeta, abstractmethod

from wheatley.aliases import Row, Places
from wheatley.stroke import Stroke, HANDSTROKE
from wheatley.row_generation.helpers import rounds


class RowGenerator(metaclass=ABCMeta):
    """ Abstract base class for behaviours common to all row generators. """

    logger_name = "ROWGEN"

    def __init__(self, stage: int) -> None:
        self.stage = stage
        self.logger = logging.getLogger(self.logger_name)

        self._has_bob = False
        self._has_single = False
        self._index = 0
        self._row = self.rounds()

    def reset(self) -> None:
        """ Reset the row generator. """
        self.logger.info("Reset")

        self._has_bob = False
        self._has_single = False
        self._index = 0
        self._row = self.rounds()

    def reset_calls(self) -> None:
        """ Clear the pending call flags. """
        self.logger.info("Reset calls")
        self._has_bob = False
        self._has_single = False

    def next_row(self, stroke: Stroke) -> Row:
        """
        Generates the next row (with no calls).  `rg.next_row(s)` is exactly equivalent to
        `rg.next_row_and_calls(s)[0]`, and does not call `_gen_row` directly.
        """
        return self.next_row_and_calls(stroke)[0]

    def next_row_and_calls(self, stroke: Stroke) -> Tuple[Row, List[str]]:
        """ Generate the next row, and mutate state accordingly. """
        self._row, calls = self._gen_row_and_calls(self._row, stroke, self._index)

        self._index += 1

        message = " ".join([str(bell) for bell in self._row])
        self.logger.info(message)

        return (self._row, calls)

    def set_bob(self) -> None:
        """ Set the flag that a bob has been made. """
        self._has_bob = True

    def set_single(self) -> None:
        """ Set the flag that a single has been made. """
        self._has_single = True

    def rounds(self) -> Row:
        """ Generate rounds of the stage given by this RowGenerator. """
        return rounds(self.stage)

    @abstractmethod
    def _gen_row(self, previous_row: Row, stroke: Stroke, index: int) -> Row:
        pass

    # If this isn't overridden by a child class, then we assume that it won't produce calls, and
    # therefore we simply return no calls on every Row).
    def _gen_row_and_calls(self, previous_row: Row, stroke: Stroke, index: int) -> Tuple[Row, List[str]]:
        return (self._gen_row(previous_row, stroke, index), [])

    def start_stroke(self) -> Stroke: # pylint: disable=no-self-use
        """ Gets the stroke of the first row.  This defaults to HANDSTROKE, but should be overridden by
        other RowGenerators if different start strokes are possible. """
        return HANDSTROKE

    def early_calls(self) -> Dict[int, List[str]]: # pylint: disable=no-self-use
        """
        Returns the calls that should be called **before** going into the changes.  This map
        goes from <number of rows before the first row of method> to <list of calls that should be
        called on that row>.  For example, if we call a 'single' at the start of Original (as in
        https://complib.org/composition/68549), then the `early_calls` should return
        `{2: ["Go Original"], 1: ["Single"]}`.

        If this is not overridden, then it is assumed that the child class doesn't want to call any
        calls, so we return a default empty set
        """
        return {}

    @abstractmethod
    def summary_string(self) -> str:
        """ Returns a short string summarising the RowGenerator.
        This should make grammatical sense when formatted with
        'Wheatley (will ring|is ringing) {summary_string}'.
        """

    def permute(self, row: Row, places: Places) -> Row:
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

            # If not in place, must swap, index is 1 less than place
            new_row[i - 1], new_row[i] = new_row[i], new_row[i - 1]
            i += 2

        return Row(new_row)
