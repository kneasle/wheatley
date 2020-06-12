HANDSTROKE_GAP = 1

class Rhythm:
    def __init__ (self, bot):
        self._handstroke_gap = HANDSTROKE_GAP
        self._bot = bot

        self._start_time = 0
        self._blow_interval = 0

        self._expected_bells = {}
        self.data_set = []

    def expect_bell (self, expected_bell, expected_blow_time, expected_stroke):
        self._expected_bells [(expected_bell, expected_stroke)] = expected_blow_time

    def add_data_point (self, blow_time, real_time):
        self.data_set.append ((blow_time, real_time))

        print (f"Dataset: {self.data_set}")

    def on_bell_ring (self, bell, stroke, real_time):
        if (bell, stroke) in self._expected_bells:
            expected_blow_time = self._expected_bells [(bell, stroke)]

            diff = self.real_time_to_blow_time (real_time) - expected_blow_time

            print (f"Off by {diff} places")

            # Add the data point to our list if either it is close enough to not be an anomaly
            # or there are fewer than 2 datapoints in our dataset, in which case we cannot
            # determine the line accurately so we should add the datapoint anyway on the 
            # basis that it's better than nothing
            if len (self.data_set) <= 1 or abs (diff) <= 0.5:
                self.add_data_point (expected_blow_time, real_time)

            del self._expected_bells [(bell, stroke)]
        else:
            print (f"Bell {bell} unexpectedly rang at stroke {'H' if stroke else 'B'}")

    def initialise_line (self, start_real_time):
        self._start_time = start_real_time
        self._blow_interval = {
            4: 0.3,
            6: 0.3,
            8: 0.3,
            10: 0.3,
            12: 0.2
        } [self._bot.stage]

        self.data_set = []
        self.add_data_point (0, start_real_time)


    # Linear algebra-style conversions between different time measurements
    def index_to_blow_time (self, row_number, place):
        return row_number * self._bot.stage + place + (row_number // 2) * self._handstroke_gap

    def blow_time_to_real_time (self, blow_time):
        return self._start_time + self._blow_interval * blow_time

    def index_to_real_time (self, row_number, place):
        return self.blow_time_to_real_time (self.index_to_blow_time (row_number, place))

    def real_time_to_blow_time (self, real_time):
        return (real_time - self._start_time) / self._blow_interval
