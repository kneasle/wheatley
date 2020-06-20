import logging

from regression import calculate_regression


class Rhythm:
    logger_name = "RHYTHM"

    def __init__ (self, handstroke_gap=1):
        self._handstroke_gap = handstroke_gap

        self.stage = 0
        self.logger = logging.getLogger(self.logger_name)

        self._start_time = 0
        self._blow_interval = 0

        self._expected_bells = {}
        self.data_set = []

    def expect_bell (self, expected_bell, row_number, index, expected_stroke):
        expected_blow_time = self.index_to_blow_time (row_number, index)
        self._expected_bells [(expected_bell, expected_stroke)] = expected_blow_time

    def add_data_point (self, blow_time, real_time, weight):
        self.data_set.append ((blow_time, real_time, weight))

        # Only calculate the regression line if there are at least two datapoints, otherwise
        # just store the datapoint
        if len (self.data_set) >= 2:
            (self._start_time, self._blow_interval) = calculate_regression (self.data_set)

    def on_bell_ring (self, bell, stroke, real_time):
        # If this bell was expected at this stroke (i.e. is being rung by someone else)
        if (bell, stroke) in self._expected_bells:
            # Figure out where the bell was expected in ringing space
            expected_blow_time = self._expected_bells [(bell, stroke)]
            diff = self.real_time_to_blow_time (real_time) - expected_blow_time

            self.logger.debug (f"Off by {diff} places")

            # If this was the first bell, then overwrite the start_time to update the regression line
            if expected_blow_time == 0:
                self._start_time = real_time

            # Calculate the weight (which will be 1 if it is either of the first two bells to be rung
            # to not skew the data from the start)
            weight = 1 # math.exp (- expected_blow_time * expected_blow_time)
            if len (self.data_set) <= 1:
                weight = 1

            # Add the bell as a datapoint with the calculated weight
            self.add_data_point (
                expected_blow_time,
                real_time,
                weight
            )

            del self._expected_bells [(bell, stroke)]
        else:
            # If this bell wasn't expected, then log that
            self.logger.warning (f"Bell {bell} unexpectedly rang at stroke {'H' if stroke else 'B'}")

    def initialise_line (self, stage, user_controls_treble, start_real_time):
        # Remove any data that's left over in the dataset
        self.data_set = []

        # Find the default blow interval for the given stage (used when the bot isn't ringing
        # both trebles)
        self.stage = stage
        self._blow_interval = {
            4: 0.3,
            6: 0.3,
            8: 0.3,
            10: 0.3,
            12: 0.2
        } [self.stage]

        if not user_controls_treble:
            # If the bot is ringing the first bell, then add it as a datapoint anyway, so that after the
            # 2nd bell is rung, a regression line can be made
            self.add_data_point (0, self._start_time, 1)
            self._start_time = start_real_time
        else:
            # If the bot isn't ringing the first bell, then set the expected time of the first bell to
            # infinity so that the bot will wait indefinitely for the first bell to ring, and then it will
            # extrapolate from that time
            self._start_time = float ('inf')


    # Linear conversions between different time measurements
    def index_to_blow_time (self, row_number, place):
        return row_number * self.stage + place + (row_number // 2) * self._handstroke_gap

    def blow_time_to_real_time (self, blow_time):
        return self._start_time + self._blow_interval * blow_time

    def index_to_real_time (self, row_number, place):
        return self.blow_time_to_real_time (self.index_to_blow_time (row_number, place))

    def real_time_to_blow_time (self, real_time):
        return (real_time - self._start_time) / self._blow_interval
