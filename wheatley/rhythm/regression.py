""" A module for the Rhythm class that detects peal speed by performing regression on the users' bells. """

import logging
import math

from typing import Any, Dict, List, Tuple

# We can disable the type checking on numpy because it is only used within this file and the interface from
# this file to the rest of the code is type-checked.
import numpy # type: ignore

from wheatley.stroke import Stroke
from wheatley.bell import Bell
from .abstract_rhythm import Rhythm


WEIGHT_REJECTION_THRESHOLD = 0.001


# ===== REGRESSION FUNCTIONS =====

def fill(index: int, item: float, length: int) -> List[float]:
    """
    Make an array that contains `length` 0s, but with the value at `index` replaced with `item`.
    """
    a = [0.0 for _ in range(length)]
    a[index] = item
    return a


def calculate_regression(data_set: List[Tuple[float, float, float]]) -> Tuple[float, float]:
    """
    Calculates a weighted linear regression over the data given in data_set.
    Expects data_set to consist of 3-tuples of (blow_time, real_time, weight).
    """
    blow_times = [b for (b, r, w) in data_set]
    real_times = [r for (b, r, w) in data_set]
    weights = [w for (b, r, w) in data_set]

    num_datapoints = len(weights)

    x = numpy.array([[1, b] for b in blow_times])
    w = numpy.array([fill(i, w, num_datapoints) for (i, w) in enumerate(weights)])
    y = numpy.array([[x] for x in real_times])

    # Calculate (X^T * W * X) * X^T * W * y
    beta = numpy.linalg.inv(x.transpose().dot(w).dot(x)).dot(x.transpose()).dot(w).dot(y)

    return beta[0][0], beta[1][0]



# ===== UTILITY FUNCTIONS =====

def peal_speed_to_blow_interval(peal_minutes: float, num_bells: int) -> float:
    """ Calculate the blow interval from the peal speed, assuming a peal of 5040 changes """
    peal_speed_seconds = peal_minutes * 60
    seconds_per_whole_pull = peal_speed_seconds / 2520  # 2520 whole pulls = 5040 rows
    return seconds_per_whole_pull / (num_bells * 2 + 1)


def inverse_lerp(a: float, b: float, c: float) -> float:
    """
    Inverse function to `lerp`.  Calculates t such that lerp(a, b, t) = c.
    (will divide by zero if a = b)
    """
    return (c - a) / (b - a)


def lerp(a: float, b: float, t: float) -> float:
    """
    Linearly interpolates (unclamped) between a and b with factor t.
    Acts such that `lerp(a, b, 0.0)` returns `a`, and `lerp(a, b, 1.0)` returns `b`.
    """
    return (1 - t) * a + t * b


# ===== RHYTHM CLASS =====

class RegressionRhythm(Rhythm):
    """
    A class that will use regression to figure out the current ringing speed and ring accordingly.
    """

    logger_name = "RHYTHM:Regression"

    def __init__(self, inertia: float, peal_speed: float=178, handstroke_gap: float=1,
                 min_bells_in_dataset: int=4, max_bells_in_dataset: int=15, initial_inertia: float=0) -> None:
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
        # Two values that determine the linear relationship between ringing and real time - these are set by
        # the regression algorithm and used to decide when Wheatley's bells should be rung
        self._start_time = 0.0
        self._blow_interval = 0.0

        # The actual time that the current touch started (this is unaffected by the regression algorithm)
        self._real_start_time = 0.0

        self._number_of_user_controlled_bells = 0
        # Maps a bell and a stroke to the row number and place which that bell is next expected to ring at
        # that stroke
        self._expected_bells: Dict[Tuple[Bell, Stroke], Tuple[int, int]] = {}
        self.data_set: List[Tuple[float, float, float]] = []

        self.logger = logging.getLogger(self.logger_name)

        self._should_return_to_mainloop = False

    def _add_data_point(self, row_number: int, place: int, real_time: float, weight: float) -> None:
        # Always manage the data set, even when inertia is 1 (in case inertia gets changed whilst
        # Wheatley is ringing)
        blow_time = self.index_to_blow_time(row_number, place)
        self.data_set.append((blow_time, real_time, weight))
        for (b, r, w) in self.data_set:
            self.logger.debug(f"Datapoint: {b:4.1f} {r - self._real_start_time:8.3f}s {w:.3f}")
        # Filter out datapoints with extremely low weights
        self.data_set = list(filter(lambda d: d[2] > WEIGHT_REJECTION_THRESHOLD, self.data_set))
        # Eventually forget about datapoints
        if len(self.data_set) >= self._max_bells_in_dataset:
            del self.data_set[0]

        # The inertia is set to 0 for the first row, to make sure that there's a smooth pullof
        inertia = self._preferred_inertia if row_number > 0 else self._initial_inertia
        # Early return if inertia == 1, since there's no point doing any regression if the result
        # will be ignored
        if inertia == 1:
            return

        # Only calculate the regression line if there are enough datapoints to gain a meaningful result
        if len(self.data_set) >= self._min_bells_in_dataset:
            (new_start_time, new_blow_interval) = calculate_regression(self.data_set)
            # Lerp between the new times and the old times, according to the desired inertia
            self._start_time = lerp(new_start_time, self._start_time, inertia)
            self._blow_interval = lerp(new_blow_interval, self._blow_interval, inertia)
            self.logger.debug(f"Start time: {self._start_time:.3f}")
            self.logger.debug(f"Bell interval: {self._blow_interval:.3f}")

    def return_to_mainloop(self) -> None:
        """
        When called, this function requires that Wheatley's main thread should return from
        wait_for_bell_time and give control back to the mainloop within a reasonable amount of time
        (i.e. 1/10 of a second is acceptable, but anything approacing a second is not)
        """
        self._should_return_to_mainloop = True

    def wait_for_bell_time(self, current_time: float, bell: Bell, row_number: int, place: int,
                           user_controlled: bool, stroke: Stroke) -> None:
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

    def expect_bell(self, expected_bell: Bell, row_number: int, place: int, expected_stroke: Stroke) -> None:
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """
        self.logger.debug(f"Expected bell {expected_bell} at index {row_number}:{place} at {expected_stroke}")
        self._expected_bells[(expected_bell, expected_stroke)] = (row_number, place)

    def change_setting(self, key: str, value: Any, real_time: float) -> None:
        def log_warning(message: str) -> None:
            self.logger.warning(f"Invalid value for setting '{key}': {message}")

        if key == "sensitivity":
            self.logger.warning(f"NOT IMPLEMENTED: setting sensitivity to {value}.")
        if key == "inertia":
            try:
                new_inertia = float(value)
                if new_inertia > 1 or new_inertia < 0:
                    log_warning(f"{new_inertia} is not between 0 and 1")
                else:
                    self._preferred_inertia = new_inertia
                    self.logger.warning(f"Setting 'self._preferred_inertia' to '{value}'")
            except ValueError:
                log_warning(f"{value} is not an number")
        if key == "peal_speed":
            new_peal_speed = int(value)
            if new_peal_speed <= 0:
                log_warning(f"{new_peal_speed} is not positive")
            else:
                self._peal_speed = new_peal_speed
                # Don't try to calculate the regression line if _blow_interval is 0 (because the lin
                # alg will cause a DivisionByZeroError).
                if self._blow_interval == 0:
                    return
                # Make sure that the `Peal Speed` control on Ringing Room can update the speed in
                # real time - this change makes no difference to the CLI version, because
                # `self._peal_speed` cannot be changed whilst Wheatley is running.  This is not a
                # long term solution (famous last words ;P), but for the initial RR release, I think
                # this should happen.
                peal_speed_interval = peal_speed_to_blow_interval(self._peal_speed, self.stage)
                current_bell_time = self.real_time_to_blow_time(real_time)
                # We want to find the line which has gradient `peal_speed_interval` and intersects with
                # our current line at the current time (so that Wheatley's perception of time doesn't
                # simply jump).
                self._blow_interval = peal_speed_interval
                self._start_time = real_time - current_bell_time * self._blow_interval
                self.logger.info(
                    f"Changing peal speed to {self._peal_speed} (bell interval {self._blow_interval:.3})"
                )

    def on_bell_ring(self, bell: Bell, stroke: Stroke, real_time: float) -> None:
        """
        Called when a bell is rung at a given stroke.  Used as a callback from the Tower class.
        """
        # If this bell was expected at this stroke (i.e. is being rung by someone else)
        if (bell, stroke) in self._expected_bells:
            # Figure out where the bell was expected in ringing space
            (row_number, place) = self._expected_bells[(bell, stroke)]
            expected_blow_time = self.index_to_blow_time(row_number, place)
            diff = self.real_time_to_blow_time(real_time) - expected_blow_time

            self.logger.debug(f"{bell} off by {diff:.3f} places")

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
            self.logger.warning(f"Bell {bell} unexpectedly rang at {stroke}")

    def initialise_line(self, stage: int, user_controls_treble: bool, start_time: float,
                        number_of_user_controlled_bells: int) -> None:
        """ Allow the Rhythm object to initialise itself when 'Look to' is called. """
        self._number_of_user_controlled_bells = number_of_user_controlled_bells
        self.stage = stage

        # Remove any data that's left over in the dataset from the last touch
        self.data_set = []

        # Calculate the blow interval from the peal speed, asuming a peal of 5040 changes
        self._blow_interval = peal_speed_to_blow_interval(self._peal_speed, self.stage)

        # Set real start time to make debug output more succinct
        self._real_start_time = start_time

        if not user_controls_treble:
            # If Wheatley is ringing the first bell, then add it as a datapoint anyway, so that after
            # the 2nd bell is rung, a regression line can be made
            self._add_data_point(0, 0, start_time, 1)
            self._start_time = start_time
        else:
            # If Wheatley isn't ringing the first bell, then set the expected time of the first bell
            # to infinity so that Wheatley will wait indefinitely for the first bell to ring, and
            # then it will extrapolate from that time
            self._start_time = float('inf')

    # Linear conversions between different time measurements
    def index_to_blow_time(self, row_number: int, place: int) -> float:
        """ Convert a row number and place into a blow_time, taking hanstroke gaps into account. """
        return row_number * self.stage + place + (row_number // 2) * self._handstroke_gap

    def blow_time_to_real_time(self, blow_time: float) -> float:
        """ Convert from blow_time into real_time using the regression line. """
        return self._start_time + self._blow_interval * blow_time

    def index_to_real_time(self, row_number: int, place: int) -> float:
        """
        Convert straight from row number and place into the expected real time according to the
        regression line.
        """
        return self.blow_time_to_real_time(self.index_to_blow_time(row_number, place))

    def real_time_to_blow_time(self, real_time: float) -> float:
        """ Convert backwards from a real time to the corresponding blow time. """
        return (real_time - self._start_time) / self._blow_interval
