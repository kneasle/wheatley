""" Contains the RowGenerator subclass for generating rows from a CompLib composition. """

from typing import List

import requests

from wheatley.bell import Bell
from .row_generator import RowGenerator


class PrivateCompError(ValueError):
    """ An error class thrown when a user tries to access a private CompLib composition. """

    def __init__(self, comp_id):
        super().__init__()

        self._comp_id = comp_id

    def __str__(self):
        return f"Composition with ID {self._comp_id} is private."


class InvalidCompError(ValueError):
    """ An error class thrown when a user tries to access an invalid CompLib composition. """

    def __init__(self, comp_id):
        super().__init__()

        self._comp_id = comp_id

    def __str__(self):
        return f"Composition with ID {self._comp_id} is does not exist."


class ComplibCompositionGenerator(RowGenerator):
    """ The RowGenerator subclass for generating rows from a CompLib composition. """

    complib_url = "https://complib.org/composition/"

    def __init__(self, comp_id: int):
        url = self.complib_url + str(comp_id) + "/rows"
        request_rows = requests.get(url)

        if request_rows.status_code == 404:
            raise InvalidCompError(comp_id)

        if request_rows.status_code == 403:
            raise PrivateCompError(comp_id)

        request_rows.raise_for_status()

        # New line separated, skip the first line (rounds)
        split_rows = request_rows.text.splitlines(False)[1::]
        self.loaded_rows = [[Bell.from_str(bell) for bell in row] for row in split_rows]

        stage = len(self.loaded_rows[0])

        super().__init__(stage)

    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        if index < len(self.loaded_rows):
            return self.loaded_rows[index]

        return self.rounds()
