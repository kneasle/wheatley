from typing import List

from bell import Bell

from .row_generator import RowGenerator


class PlainHuntGenerator(RowGenerator):
    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        if is_handstroke:
            return self.permute(previous_row, [])

        return self.permute(previous_row, [1, self.stage])
