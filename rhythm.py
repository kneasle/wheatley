HANDSTROKE_GAP = 1

class Rhythm:
    def __init__ (self, bot):
        self._handstroke_gap = HANDSTROKE_GAP
        self._bot = bot

        self._start_time = 0
        self._blow_interval = 0

        self._expected_bells = {}

    def expect_bell (self, expected_bell, expected_time, expected_stroke):
        print (f"Expecting {expected_bell} at {expected_time} on {'H' if expected_stroke else 'B'}")

        self._expected_bells [expected_bell] = (expected_time, expected_stroke)

    def on_bell_ring (self, bell, stroke):
        print (f"Heard bell {bell} on stroke {stroke}")

    def initialise_line (self, start_real_time):
        self._start_time = start_real_time
        self._blow_interval = {
            4: 0.3,
            6: 0.3,
            8: 0.3,
            10: 0.3,
            12: 0.2
        } [self._bot.stage]


    # Linear algebra-style conversions between different time measurements
    def index_to_blow_time (self, row_number, place):
        return row_number * self._bot.stage + place + (row_number // 2) * self._handstroke_gap

    def blow_time_to_real_time (self, blow_time):
        return self._start_time + self._blow_interval * blow_time

    def index_to_real_time (self, row_number, place):
        return self.blow_time_to_real_time (self.index_to_blow_time (row_number, place))
