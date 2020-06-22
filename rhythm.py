import logging
import math

from abc import ABCMeta, abstractmethod
from time import sleep

from bell import Bell
from regression import calculate_regression


MAX_CHANGES_IN_DATASET = 3.0
WEIGHT_REJECTION_THRESHOLD = 0.001
# An inertia-like coefficient designed to allow the regression finder to slowly adjust to
# a new rhythm
# 0.0 means that a new regression line will take effect instantly
# 1.0 means that no effect is made at all
REGRESSION_INERTIA_COEFFICIENT = 0.5


# Calculates t such that lerp(a, b, t) = c (will divide by zero if a = b)
def inverse_lerp(a, b, c):
    return (c - a) / (b - a)


def lerp(a, b, t):
    return (1 - t) * a + t * b


class Rhythm(metaclass=ABCMeta):
    @abstractmethod
    def wait_for_bell_time(self, current_time: float, bell: Bell, row_number: int, place: int,
                           user_controlled: bool, stroke: bool):
        pass

    @abstractmethod
    def expect_bell(self, expected_bell: Bell, row_number: int, index: int, expected_stroke: bool):
        pass

    @abstractmethod
    def on_bell_ring(self, bell: Bell, stroke: bool, real_time: float):
        pass

    @abstractmethod
    def initialise_line(self, stage: int, user_controls_treble: bool, start_time: float,
                        number_of_user_controlled_bells: int):
        pass


class WaitForUserRhythm(Rhythm):
    logger_name = "RHYTHM:WaitForUser"

    def __init__(self, rhythm: Rhythm):
        self._innerRhythm = rhythm
        self._expected_bells = set()
        self.delay = 0
        self.logger = logging.getLogger(self.logger_name)

    def wait_for_bell_time(self, current_time, bell, row_number, place, user_controlled, stroke):
        self._innerRhythm.wait_for_bell_time(current_time - self.delay, bell, row_number, place,
                                             user_controlled, stroke)
        if user_controlled:
            delay_for_user = 0
            while (bell, stroke) in self._expected_bells:
                sleep(0.01)
                delay_for_user += 0.01
                self.logger.debug(f"Waiting for {bell}")
            if delay_for_user:
                self.logger.info(f"Delayed for {delay_for_user}")
                self.delay += delay_for_user

    def expect_bell(self, expected_bell, row_number, index, expected_stroke):
        self._innerRhythm.expect_bell(expected_bell, row_number, index, expected_stroke)
        self._expected_bells.add((expected_bell, expected_stroke))

    def on_bell_ring(self, bell, stroke, real_time):
        self._innerRhythm.on_bell_ring(bell, stroke, real_time - self.delay)
        try:
            self._expected_bells.remove((bell, stroke))
        except KeyError:
            pass

    def initialise_line(self, stage, user_controls_treble, start_time,
                        number_of_user_controlled_bells):
        self._innerRhythm.initialise_line(stage, user_controls_treble, start_time - self.delay,
                                          number_of_user_controlled_bells)


class RegressionRhythm(Rhythm):
    logger_name = "RHYTHM:Regression"

    def __init__(self, handstroke_gap=1):
        self._handstroke_gap = handstroke_gap

        self.stage = 0
        self.logger = logging.getLogger(self.logger_name)

        self._start_time = 0
        self._blow_interval = 0

        self._number_of_user_controlled_bells = 0

        self._expected_bells = {}
        self.data_set = []

    def expect_bell(self, expected_bell, row_number, index, expected_stroke):
        self.logger.debug(f"Expected bell {expected_bell} at index {row_number}:{index} at stroke" \
                            + "{expected_stroke}")
        expected_blow_time = self.index_to_blow_time(row_number, index)
        self._expected_bells[(expected_bell, expected_stroke)] = expected_blow_time

    def add_data_point(self, blow_time, real_time, weight):
        self.data_set.append((blow_time, real_time, weight))

        for (blow_time, real_time, weight) in self.data_set:
            self.logger.debug(f"  {blow_time}\t{real_time}\t{weight}")

        max_dataset_length = MAX_CHANGES_IN_DATASET * self._number_of_user_controlled_bells

        # Only calculate the regression line if there are at least two datapoints, otherwise
        # just store the datapoint
        if len(self.data_set) >= 2:
            (new_start_time, new_blow_interval) = calculate_regression(self.data_set)

            # Lerp between the new times and the old times, according to the desired inertia
            regression_inertia = REGRESSION_INERTIA_COEFFICIENT

            self._start_time = lerp(new_start_time, self._start_time, regression_inertia)
            self._blow_interval = lerp(new_blow_interval, self._blow_interval, regression_inertia)

            self.logger.debug(f"Bell interval: {self._blow_interval}")

            # Filter out datapoints with extremely low weights
            self.data_set = list(filter(lambda d: d[2] > WEIGHT_REJECTION_THRESHOLD, self.data_set))

            # Eventually forget about datapoints
            if len(self.data_set) >= max_dataset_length:
                del self.data_set[0]

    def on_bell_ring(self, bell, stroke, real_time):
        # If this bell was expected at this stroke (i.e. is being rung by someone else)
        if (bell, stroke) in self._expected_bells:
            # Figure out where the bell was expected in ringing space
            expected_blow_time = self._expected_bells[(bell, stroke)]
            diff = self.real_time_to_blow_time(real_time) - expected_blow_time

            self.logger.info(f"{bell} off by {diff} places")

            # If this was the first bell, then overwrite the start_time to update
            # the regression line
            if expected_blow_time == 0:
                self._start_time = real_time

            # Calculate the weight (which will be 1 if it is either of the first two bells to be
            # rung to not skew the data from the start)
            weight = math.exp(- diff ** 2)
            if len(self.data_set) <= 1:
                weight = 1

            # Add the bell as a datapoint with the calculated weight
            self.add_data_point(
                expected_blow_time,
                real_time,
                weight
            )

            del self._expected_bells[(bell, stroke)]
        else:
            # If this bell wasn't expected, then log that
            self.logger.warning(f"Bell {bell} unexpectedly rang at stroke {'H' if stroke else 'B'}")

    def initialise_line(self, stage, user_controls_treble, start_real_time,
                        number_of_user_controlled_bells):
        self._number_of_user_controlled_bells = number_of_user_controlled_bells

        # Remove any data that's left over in the dataset from the last touch
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
        }[self.stage]

        if not user_controls_treble:
            # If the bot is ringing the first bell, then add it as a datapoint anyway, so that after
            # the 2nd bell is rung, a regression line can be made
            self.add_data_point(0, start_real_time, 1)
            self._start_time = start_real_time
        else:
            # If the bot isn't ringing the first bell, then set the expected time of the first bell
            # to infinity so that the bot will wait indefinitely for the first bell to ring, and 
            # then it will extrapolate from that time
            self._start_time = float('inf')

    def wait_for_bell_time(self, current_time, bell, row_number, place, user_controlled, stroke):
        if user_controlled and self._start_time == float('inf'):
            self.logger.debug(f"Waiting for pull off")
            while self._start_time == float('inf'):
                sleep(0.01)
            self.logger.debug(f"Pulled off")
            return

        bell_time = self.index_to_real_time(row_number, place)
        if bell_time == float('inf') or self._start_time == 0:
            self.logger.error(f"Bell Time {bell_time}; Start Time {self._start_time}")
            sleep(self._blow_interval or 0.2)
        elif bell_time > current_time:
            sleep(bell_time - current_time)
        else:
            # Slow the ticks slightly
            sleep(0.01)

    # Linear conversions between different time measurements
    def index_to_blow_time(self, row_number, place):
        return row_number * self.stage + place + (row_number // 2) * self._handstroke_gap

    def blow_time_to_real_time(self, blow_time):
        return self._start_time + self._blow_interval * blow_time

    def index_to_real_time(self, row_number, place):
        return self.blow_time_to_real_time(self.index_to_blow_time(row_number, place))

    def real_time_to_blow_time(self, real_time):
        return (real_time - self._start_time) / self._blow_interval
