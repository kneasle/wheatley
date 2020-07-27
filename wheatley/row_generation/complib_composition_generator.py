""" Contains the RowGenerator subclass for generating rows from a CompLib composition. """

from typing import List

import requests

from wheatley.bell import Bell
from .row_generator import RowGenerator


class ComplibCompositionGenerator(RowGenerator):
    """ The RowGenerator subclass for generating rows from a CompLib composition. """

    complib_url = "https://complib.org/composition/"

    def __init__(self, comp_id: int):
        url = self.complib_url + str(comp_id) + "/rows"
        request_rows = requests.get(url)
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
