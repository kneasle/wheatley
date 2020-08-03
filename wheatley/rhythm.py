"""
A module to handle the 'rhythm' of the bot - i.e. to keep track of when bells should ring,
based on when the user-controlled bells ring.
"""

import logging
import math

from abc import ABCMeta, abstractmethod
from time import sleep

from wheatley.bell import Bell
from wheatley.regression import calculate_regression


WEIGHT_REJECTION_THRESHOLD = 0.001


def inverse_lerp(a, b, c):
    """
    Inverse function to `lerp`.  Calculates t such that lerp(a, b, t) = c.
    (will divide by zero if a = b)
    """

    return (c - a) / (b - a)


def lerp(a, b, t):
    """
    Linearly interpolates (unclamped) between a and b with factor t.
    Acts such that `lerp(a, b, 0.0)` returns `a`, and `lerp(a, b, 1.0)` returns `b`.
    """

    return (1 - t) * a + t * b


class Rhythm(metaclass=ABCMeta):
    """
    An abstract Rhythm class, used as an interface by the Bot class to interact with Rhythms.
    """

    @abstractmethod
    def wait_for_bell_time(self, current_time: float, bell: Bell, row_number: int, place: int,
                           user_controlled: bool, stroke: bool):
        """ Sleeps the thread until a given Bell should have rung. """

        pass

    @abstractmethod
    def expect_bell(self, expected_bell: Bell, row_number: int, place: int, expected_stroke: bool):
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """

        pass

    @abstractmethod
    def on_bell_ring(self, bell: Bell, stroke: bool, real_time: float):
        """
        Called when a bell is rung at a given stroke.  Used as a callback from the Tower class.
        """

        pass

    @abstractmethod
    def initialise_line(self, stage: int, user_controls_treble: bool, start_time: float,
                        number_of_user_controlled_bells: int):
        """ Allow the Rhythm object to initialise itself when 'Look to' is called. """

        pass


class WaitForUserRhythm(Rhythm):
    """ A decorator class that adds the ability to wait for user-controlled bells to ring. """

    logger_name = "RHYTHM:WaitForUser"

    def __init__(self, rhythm: Rhythm):
        """
        Initialise a wrapper around another Rhythm class that will decorate that class with the
        ability to wait for other people to ring.
        """

        self._inner_rhythm = rhythm
        self._expected_bells = set()
        self.delay = 0
        self.logger = logging.getLogger(self.logger_name)

    def wait_for_bell_time(self, current_time, bell, row_number, place, user_controlled, stroke):
        """ Sleeps the thread until a given Bell should have rung. """

        self._inner_rhythm.wait_for_bell_time(current_time - self.delay, bell, row_number, place,
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

    def expect_bell(self, expected_bell, row_number, place, expected_stroke):
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """

        self._inner_rhythm.expect_bell(expected_bell, row_number, place, expected_stroke)
        self._expected_bells.add((expected_bell, expected_stroke))

    def on_bell_ring(self, bell, stroke, real_time):
        """
        Called when a bell is rung at a given stroke.  Used as a callback from the Tower class.
        """

        self._inner_rhythm.on_bell_ring(bell, stroke, real_time - self.delay)
        try:
            self._expected_bells.remove((bell, stroke))
        except KeyError:
            pass

    def initialise_line(self, stage, user_controls_treble, start_time,
                        number_of_user_controlled_bells):
        """ Allow the Rhythm object to initialise itself when 'Look to' is called. """

        self._inner_rhythm.initialise_line(stage, user_controls_treble, start_time - self.delay,
                                           number_of_user_controlled_bells)


class RegressionRhythm(Rhythm):
    """
    A class that will use regression to figure out the current ringing speed and ring accordingly.
    """

    logger_name = "RHYTHM:Regression"

    def __init__(self, inertia, peal_speed=178, handstroke_gap=1, max_rows_in_dataset=3.0):
        """
        Initialises a new RegressionRhythm with a given default peal speed and handstroke gap.
        `peal_speed` is the number of minutes in a peal of 5040 changes, and `handstroke_gap`
        measures how many places long the handstroke gap is.
        """

        # An inertia-like coefficient designed to allow the regression finder to slowly adjust to
        # a new rhythm
        # 0.0 means that a new regression line will take effect instantly
        # 1.0 means that no effect is made at all
        self._preferred_inertia = inertia

        self._peal_speed = peal_speed
        self._handstroke_gap = handstroke_gap
        self._max_rows_in_dataset = max_rows_in_dataset

        self.stage = 0
        self.logger = logging.getLogger(self.logger_name)

        self._start_time = 0
        self._blow_interval = 0

        self._number_of_user_controlled_bells = 0

        self._expected_bells = {}
        self.data_set = []

    def _add_data_point(self, row_number, place, real_time, weight):
        blow_time = self.index_to_blow_time(row_number, place)

        self.data_set.append((blow_time, real_time, weight))

        for (b, r, w) in self.data_set:
            self.logger.debug(f"  {b}\t{r}\t{w}")

        max_dataset_length = self._max_rows_in_dataset * self._number_of_user_controlled_bells

        # Only calculate the regression line if there are at least two datapoints, otherwise
        # just store the datapoint
        if len(self.data_set) >= 2:
            (new_start_time, new_blow_interval) = calculate_regression(self.data_set)

            # Lerp between the new times and the old times, according to the desired inertia
            # The inertia is set to 0 for the first change, to make sure that there's a smooth
            # pullof
            regression_preferred_inertia = self._preferred_inertia if row_number > 0 else 0.0

            self._start_time = lerp(new_start_time, self._start_time, regression_preferred_inertia)
            self._blow_interval = lerp(new_blow_interval, self._blow_interval,
                                       regression_preferred_inertia)

            self.logger.debug(f"Bell interval: {self._blow_interval}")

            # Filter out datapoints with extremely low weights
            self.data_set = list(filter(lambda d: d[2] > WEIGHT_REJECTION_THRESHOLD, self.data_set))

            # Eventually forget about datapoints
            if len(self.data_set) >= max_dataset_length:
                del self.data_set[0]

    def wait_for_bell_time(self, current_time, bell, row_number, place, user_controlled, stroke):
        """ Sleeps the thread until a given Bell should have rung. """

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

    def expect_bell(self, expected_bell, row_number, place, expected_stroke):
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """

        self.logger.debug(f"Expected bell {expected_bell} at index {row_number}:{place} at stroke" \
                            + f"{expected_stroke}")
        self._expected_bells[(expected_bell, expected_stroke)] = (row_number, place)

    def on_bell_ring(self, bell, stroke, real_time):
        """
        Called when a bell is rung at a given stroke.  Used as a callback from the Tower class.
        """

        # If this bell was expected at this stroke (i.e. is being rung by someone else)
        if (bell, stroke) in self._expected_bells:
            # Figure out where the bell was expected in ringing space
            (row_number, place) = self._expected_bells[(bell, stroke)]

            expected_blow_time = self.index_to_blow_time(row_number, place)

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
            self._add_data_point(
                row_number,
                place,
                real_time,
                weight
            )

            del self._expected_bells[(bell, stroke)]
        else:
            # If this bell wasn't expected, then log that
            self.logger.warning(f"Bell {bell} unexpectedly rang at stroke {'H' if stroke else 'B'}")

    def initialise_line(self, stage, user_controls_treble, start_time,
                        number_of_user_controlled_bells):
        """ Allow the Rhythm object to initialise itself when 'Look to' is called. """

        self._number_of_user_controlled_bells = number_of_user_controlled_bells
        self.stage = stage

        # Remove any data that's left over in the dataset from the last touch
        self.data_set = []

        # Calculate the blow interval from the peal speed, asuming a peal of 5040 changes
        peal_speed_seconds = self._peal_speed * 60
        seconds_per_whole_pull = peal_speed_seconds / 2520  # 2520 = 5040 / 2
        self._blow_interval = seconds_per_whole_pull / (self.stage * 2 + 1)

        if not user_controls_treble:
            # If the bot is ringing the first bell, then add it as a datapoint anyway, so that after
            # the 2nd bell is rung, a regression line can be made
            self._add_data_point(0, 0, start_time, 1)
            self._start_time = start_time
        else:
            # If the bot isn't ringing the first bell, then set the expected time of the first bell
            # to infinity so that the bot will wait indefinitely for the first bell to ring, and
            # then it will extrapolate from that time
            self._start_time = float('inf')

    # Linear conversions between different time measurements
    def index_to_blow_time(self, row_number, place):
        """ Convert a row number and place into a blow_time, taking hanstroke gaps into account. """

        return row_number * self.stage + place + (row_number // 2) * self._handstroke_gap

    def blow_time_to_real_time(self, blow_time):
        """ Convert from blow_time into real_time using the regression line. """

        return self._start_time + self._blow_interval * blow_time

    def index_to_real_time(self, row_number, place):
        """
        Convert straight from row number and place into the expected real time according to the
        regression line.
        """

        return self.blow_time_to_real_time(self.index_to_blow_time(row_number, place))

    def real_time_to_blow_time(self, real_time):
        """ Convert backwards from a real time to the corresponding blow time. """

        return (real_time - self._start_time) / self._blow_interval
