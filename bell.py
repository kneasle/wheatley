class Bell:
    @classmethod
    def from_str(cls, bell_str: str):
        try:
            index = Bell._lookup_name.index(bell_str)
        except ValueError:
            raise ValueError(f"'{bell_str}' is not known bell symbol")
        return cls(index)

    @classmethod
    def from_number(cls, bell_num: int):
        return cls(bell_num - 1)

    @classmethod
    def from_index(cls, bell_index: int):
        return cls(bell_index)

    def __init__(self, index: int):
        if index < 0 or index >= len(self._lookup_name):
            raise ValueError(f"'{index}' is not known bell index")
        self.index = index

    @property
    def number(self):
        return self.index + 1

    _lookup_name = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "E", "T"]

    def __str__(self):
        return self._lookup_name[self.index]

    def __eq__(self, other):
        return isinstance(other, Bell) and other.index == self.index

    def __hash__(self):
        return self.index
