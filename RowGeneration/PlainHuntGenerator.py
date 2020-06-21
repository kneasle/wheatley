from typing import List

from RowGeneration.RowGenerator import RowGenerator
from bell import Bell


class PlainHuntGenerator(RowGenerator):
    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        if is_handstroke:
            return self.permute(previous_row, [])
        else:
            return self.permute(previous_row, [1, self.stage])
