from typing import List

import requests

from RowGeneration.Helpers import convert_bell_string
from RowGeneration.RowGenerator import RowGenerator


class ComplibCompositionReader(RowGenerator):
    complib_url = "https://complib.org/composition/"

    def __init__(self, id: int, auto_start=True):
        url = self.complib_url + str(id) + "/rows"
        request_rows = requests.get(url)
        request_rows.raise_for_status()

        # New line separated, skip the first line (rounds)
        split_rows = request_rows.text.splitlines(False)[1::]
        self.loaded_rows = [[convert_bell_string(bell) for bell in row] for row in split_rows]

        stage = len(self.loaded_rows[0])
        super().__init__(stage, auto_start)

    def _gen_row(self, previous_row: List[int], is_handstroke: bool, index: int) -> List[int]:
        if index < len(self.loaded_rows):
            return self.loaded_rows[index]
        return self.rounds()
