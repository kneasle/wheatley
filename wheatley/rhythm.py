"""
A module to handle the 'rhythm' of the bot - i.e. to keep track of when bells should ring,
based on when the user-controlled bells ring.
"""

import logging
import math
import time

from abc import ABCMeta, abstractmethod
from typing import Any

from wheatley.bell import Bell
from wheatley.regression import calculate_regression
from wheatley.tower import HANDSTROKE, BACKSTROKE, stroke_to_string


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
    def return_to_mainloop(self):
        """
        When called, this function requires that Wheatley's main thread should return from
        wait_for_bell_time and give control back to the mainloop within a reasonable amount of time
        (i.e. 1/10 of a second is acceptable, but anything approacing a second is not)
        """

    @abstractmethod
    def wait_for_bell_time(self, current_time: float, bell: Bell, row_number: int, place: int,
                           user_controlled: bool, stroke: bool):
        """ Sleeps the thread until a given Bell should have rung. """

    @abstractmethod
    def expect_bell(self, expected_bell: Bell, row_number: int, place: int, expected_stroke: bool):
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """

    @abstractmethod
    def change_setting(self, key: str, value: Any):
        """ Called when the Ringing Room server asks Wheatley to change a setting. """

    @abstractmethod
    def on_bell_ring(self, bell: Bell, stroke: bool, real_time: float):
        """
        Called when a bell is rung at a given stroke.  Used as a callback from the Tower class.
        """

    @abstractmethod
    def initialise_line(self, stage: int, user_controls_treble: bool, start_time: float,
                        number_of_user_controlled_bells: int):
        """ Allow the Rhythm object to initialise itself when 'Look to' is called. """

    def sleep(self, seconds: float): #  pylint: disable=no-self-use
        """ Sleeps for given number of seconds. Allows mocking in tests"""
        time.sleep(seconds)


class WaitForUserRhythm(Rhythm):
    """ A decorator class that adds the ability to wait for user-controlled bells to ring. """

    logger_name = "RHYTHM:WaitForUser"
    sleep_time = 0.01

    def __init__(self, rhythm: Rhythm):
        """
        Initialise a wrapper around another Rhythm class that will decorate that class with the
        ability to wait for other people to ring.
        """
        self._inner_rhythm = rhythm

        self._current_stroke = HANDSTROKE

        self._expected_bells = {HANDSTROKE: set(), BACKSTROKE: set()}
        self._early_bells = {HANDSTROKE: set(), BACKSTROKE: set()}

        self.delay = 0

        self.logger = logging.getLogger(self.logger_name)

        self._should_return_to_mainloop = False

    def return_to_mainloop(self):
        """
        When called, this function requires that Wheatley's main thread should return from
        wait_for_bell_time and give control back to the mainloop within a reasonable amount of time
        (i.e. 1/10 of a second is acceptable, but anything approacing a second is not)
        """
        self._should_return_to_mainloop = True
        self._inner_rhythm.return_to_mainloop()

    def wait_for_bell_time(self, current_time, bell, row_number, place, user_controlled, stroke):
        """ Sleeps the thread until a given Bell should have rung. """
        if stroke != self._current_stroke:
            self.logger.debug(f"Switching to unexpected stroke {stroke_to_string(stroke)}")
            self._current_stroke = stroke

        self._inner_rhythm.wait_for_bell_time(current_time - self.delay, bell, row_number, place,
                                              user_controlled, stroke)
        if user_controlled:
            delay_for_user = 0
            while bell in self._expected_bells[stroke]:
                self.sleep(self.sleep_time)
                delay_for_user += self.sleep_time
                self.logger.debug(f"Waiting for {bell}")
                if self._should_return_to_mainloop:
                    break

            if delay_for_user:
                self.delay += delay_for_user
                self.logger.info(f"Delayed for {delay_for_user}")

        # Reset the flag to say that we've returned to the mainloop
        self._should_return_to_mainloop = False

    def expect_bell(self, expected_bell, row_number, place, expected_stroke):
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """
        self._inner_rhythm.expect_bell(expected_bell, row_number, place, expected_stroke)

        if expected_stroke != self._current_stroke:
            self._current_stroke = expected_stroke
            self._expected_bells[expected_stroke].clear()
            self._early_bells[not expected_stroke].clear()

        if expected_bell not in self._early_bells[expected_stroke]:
            self._expected_bells[expected_stroke].add(expected_bell)

    def change_setting(self, key, value):
        self._inner_rhythm.change_setting(key, value)

    def on_bell_ring(self, bell, stroke, real_time):
        """
        Called when a bell is rung at a given stroke.  Used as a callback from the Tower class.
        """
        self._inner_rhythm.on_bell_ring(bell, stroke, real_time - self.delay)

        if stroke == self._current_stroke:
            try:
                self._expected_bells[self._current_stroke].remove(bell)
            except KeyError:
                pass
            else:
                self.logger.debug(f"{bell} rung at {stroke_to_string(stroke)}")

            try:
                self._early_bells[not self._current_stroke].remove(bell)
            except KeyError:
                pass
            else:
                self.logger.debug(f"{bell} reset to {stroke_to_string(stroke)}")
        else:
            self.logger.debug(f"{bell} rung early to {stroke_to_string(stroke)}")
            self._early_bells[not self._current_stroke].add(bell)

    def initialise_line(self, stage, user_controls_treble, start_time,
                        number_of_user_controlled_bells):
        """ Allow the Rhythm object to initialise itself when 'Look to' is called. """
        self._expected_bells[HANDSTROKE].clear()
        self._expected_bells[BACKSTROKE].clear()

        self._early_bells[HANDSTROKE].clear()
        self._early_bells[BACKSTROKE].clear()

        self._current_stroke = HANDSTROKE

        # Clear any current waiting loops
        self.sleep(2 * self.sleep_time)

        self._inner_rhythm.initialise_line(stage, user_controls_treble, start_time - self.delay,
                                           number_of_user_controlled_bells)


class RegressionRhythm(Rhythm):
    """
    A class that will use regression to figure out the current ringing speed and ring accordingly.
    """

    logger_name = "RHYTHM:Regression"

    def __init__(self, inertia, peal_speed=178, handstroke_gap=1, min_bells_in_dataset=4,
                 max_bells_in_dataset=15, initial_inertia=0):
        """
        Initialises a new RegressionRhythm with a given default peal speed and handstroke gap.
        `peal_speed` is the number of minutes in a peal of 5040 changes, and `handstroke_gap`
        measures how many places long the handstroke gap is.  `initial_inertia` sets the inertia for only
        the first row, to aid with a smooth pulloff.
        """
        # An inertia-like coefficient designed to allow the regression finder to slowly adjust to
        # a new rhythm
        # 0.0 means that a new regression line will take effect instantly
        # 1.0 means that no effect is made at all
        self._preferred_inertia = inertia
        self._initial_inertia = initial_inertia

        self._peal_speed = peal_speed
        self._handstroke_gap = handstroke_gap
        self._min_bells_in_dataset = min_bells_in_dataset
        self._max_bells_in_dataset = max_bells_in_dataset

        self.stage = 0
        self._start_time = 0
        self._blow_interval = 0

        self._number_of_user_controlled_bells = 0
        self._expected_bells = {}
        self.data_set = []

        self.logger = logging.getLogger(self.logger_name)

        self._should_return_to_mainloop = False

    def _add_data_point(self, row_number, place, real_time, weight):
        blow_time = self.index_to_blow_time(row_number, place)

        self.data_set.append((blow_time, real_time, weight))

        for (b, r, w) in self.data_set:
            self.logger.debug(f"  {b}\t{r}\t{w}")

        # Only calculate the regression line if there are at least two datapoints, otherwise
        # just store the datapoint
        if len(self.data_set) >= self._min_bells_in_dataset:
            (new_start_time, new_blow_interval) = calculate_regression(self.data_set)

            # Lerp between the new times and the old times, according to the desired inertia
            # The inertia is set to 0 for the first change, to make sure that there's a smooth
            # pullof
            regression_preferred_inertia = self._preferred_inertia if row_number > 0 else \
                                           self._initial_inertia

            self._start_time = lerp(new_start_time, self._start_time, regression_preferred_inertia)
            self._blow_interval = lerp(new_blow_interval, self._blow_interval,
                                       regression_preferred_inertia)

            self.logger.debug(f"Bell interval: {self._blow_interval}")

            # Filter out datapoints with extremely low weights
            self.data_set = list(filter(lambda d: d[2] > WEIGHT_REJECTION_THRESHOLD, self.data_set))

            # Eventually forget about datapoints
            if len(self.data_set) >= self._max_bells_in_dataset:
                del self.data_set[0]

    def return_to_mainloop(self):
        """
        When called, this function requires that Wheatley's main thread should return from
        wait_for_bell_time and give control back to the mainloop within a reasonable amount of time
        (i.e. 1/10 of a second is acceptable, but anything approacing a second is not)
        """
        self._should_return_to_mainloop = True

    def wait_for_bell_time(self, current_time, bell, row_number, place, user_controlled, stroke):
        """ Sleeps the thread until a given Bell should have rung. """
        if user_controlled and self._start_time == float('inf'):
            self.logger.debug("Waiting for pull off")

            while self._start_time == float('inf'):
                self.sleep(0.01)

            self.logger.debug("Pulled off")

            return

        bell_time = self.index_to_real_time(row_number, place)
        if bell_time == float('inf') or self._start_time == 0:
            self.logger.error(f"Bell Time {bell_time}; Start Time {self._start_time}")
            self.sleep(self._blow_interval or 0.2)
        elif bell_time > current_time:
            self.sleep(bell_time - current_time)
        else:
            # Slow the ticks slightly
            self.sleep(0.01)

        self._should_return_to_mainloop = False

    def expect_bell(self, expected_bell, row_number, place, expected_stroke):
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """
        self.logger.debug(f"Expected bell {expected_bell} at index {row_number}:{place} at stroke"
                          + f"{expected_stroke}")
        self._expected_bells[(expected_bell, expected_stroke)] = (row_number, place)

    def change_setting(self, key, value):
        def log_warning(message):
            self.logger.warning(f"Invalid value for setting '{key}': {message}")

        if key == "sensitivity":
            self.logger.warning(f"NOT IMPLEMENTED: setting sensitivity to {value}.")

        if key == 'inertia':
            try:
                new_inertia = float(value)

                if new_inertia > 1 or new_inertia < 0:
                    log_warning(f"{new_inertia} is not between 0 and 1")
                else:
                    self._preferred_inertia = new_inertia

                    self.logger.warning(f"Setting 'self._preferred_inertia' to '{value}'")
            except ValueError:
                log_warning(f"{value} is not an number")


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
