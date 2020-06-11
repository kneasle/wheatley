from typing import List

from RowGeneration.RowGenerator import RowGenerator


class PlainHuntGenerator(RowGenerator):
    def _gen_row(self, previous_row: List[int], is_handstroke: bool, index: int) -> List[int]:
        if is_handstroke:
            return self.permute(previous_row, [])
        else:
            return self.permute(previous_row, [1, self.stage])
