""" A module for the Rhythm decorator class that adds the ability to wait for human ringers. """

import logging

from collections import defaultdict
from typing import Any, Dict, Set, List

from wheatley.stroke import Stroke, HANDSTROKE, BACKSTROKE
from wheatley.bell import Bell
from .abstract_rhythm import Rhythm



class WaitForUserRhythm(Rhythm):
    """ A decorator class that adds the ability to wait for user-controlled bells to ring. """

    logger_name = "RHYTHM:WaitForUser"
    sleep_time = 0.01

    def __init__(self, rhythm: Rhythm) -> None:
        """
        Initialise a wrapper around another Rhythm class that will decorate that class with the
        ability to wait for other people to ring.
        """
        self._inner_rhythm = rhythm

        self._current_stroke = HANDSTROKE

        self._rung_bells: Dict[Stroke, Dict[str, Set]] = {HANDSTROKE: defaultdict(lambda: set()), BACKSTROKE: defaultdict(lambda: set())}
        self._early_bells: Dict[Stroke, Set] = {HANDSTROKE: set(), BACKSTROKE: set()}
        self._bells_to_user: Dict[Bell, str] = {}
        self._wait_user_count: Dict[str, int] = defaultdict(lambda: 0)

        self.delay = 0.0

        self.logger = logging.getLogger(self.logger_name)

        self._should_return_to_mainloop = False

    def return_to_mainloop(self) -> None:
        """
        When called, this function requires that Wheatley's main thread should return from
        wait_for_bell_time and give control back to the mainloop within a reasonable amount of time
        (i.e. 1/10 of a second is acceptable, but anything approaching a second is not)
        """
        self._should_return_to_mainloop = True
        self._inner_rhythm.return_to_mainloop()

    def wait_for_bell_time(self, current_time: float, bell: Bell, row_number: int, place: int,
                           user_controlled: bool, stroke: Stroke) -> None:
        """ Sleeps the thread until a given Bell should have rung. """
        if stroke != self._current_stroke:
            self.logger.debug(f"Switching to unexpected stroke {stroke}")
            self._current_stroke = stroke

        self._inner_rhythm.wait_for_bell_time(current_time - self.delay, bell, row_number, place,
                                              user_controlled, stroke)
        if user_controlled:
            delay_for_user = 0.0
            user = self._bells_to_user[bell]
            self._wait_user_count[user] += 1

            self.logger.debug(f"Waiting for {bell}: {user}...")

            while self._wait_user_count[user] > len(self._rung_bells[stroke][user]):
                self.sleep(self.sleep_time)
                delay_for_user += self.sleep_time
                if self._should_return_to_mainloop:
                    self.logger.debug("Returning to mainloop")
                    break
            self.logger.debug(f"Finished waiting for {bell}")

            if delay_for_user:
                self.delay += delay_for_user
                self.logger.debug(f"Delayed for {delay_for_user:.3f}s")

        # Reset the flag to say that we've returned to the mainloop
        self._should_return_to_mainloop = False

    def expect_bell(self, expected_bell: Bell, user: str, row_number: int, place: int, expected_stroke: Stroke) -> None:
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """
        self._inner_rhythm.expect_bell(expected_bell, user, row_number, place, expected_stroke)

        # Start of a new row
        if expected_stroke != self._current_stroke:
            self._current_stroke = expected_stroke
            self._rung_bells[expected_stroke].clear()
            self._early_bells[expected_stroke.opposite()].clear()
            self._wait_user_count.clear()

        # If a bell has rung early (so is already at expected_stroke) mark it as already rung
        if expected_bell in self._early_bells[expected_stroke]:
            self._rung_bells[expected_stroke][user].add(expected_stroke)

        self._bells_to_user[expected_bell] = user

    def change_setting(self, key: str, value: Any, real_time: float) -> None:
        # Keep lying to _inner_rhythm about what the current time is
        self._inner_rhythm.change_setting(key, value, real_time - self.delay)

    def on_bell_ring(self, bell: Bell, stroke: Stroke, real_time: float) -> None:
        """
        Called when a bell is rung at a given stroke.  Used as a callback from the Tower class.
        """
        self._inner_rhythm.on_bell_ring(bell, stroke, real_time - self.delay)

        if stroke == self._current_stroke:
            user = self._bells_to_user[bell]
            self._rung_bells[self._current_stroke][user].add(bell)
            self.logger.debug(f"{bell} rung at {stroke}")

            # If bell had rung early, but rung again onto correct stroke
            try:
                self._early_bells[self._current_stroke.opposite()].remove(bell)
            except KeyError:
                pass
            else:
                self.logger.debug(f"{bell} reset to {stroke}")
        else:
            self.logger.debug(f"{bell} rung early to {stroke}")
            self._early_bells[self._current_stroke.opposite()].add(bell)

    def initialise_line(self, stage: int, user_controls_treble: bool, start_time: float,
                        number_of_user_controlled_bells: int) -> None:
        """ Allow the Rhythm object to initialise itself when 'Look to' is called. """
        self._rung_bells[HANDSTROKE].clear()
        self._rung_bells[BACKSTROKE].clear()

        self._early_bells[HANDSTROKE].clear()
        self._early_bells[BACKSTROKE].clear()

        self._current_stroke = HANDSTROKE

        # Clear any current waiting loops
        self.sleep(2 * self.sleep_time)

        self._inner_rhythm.initialise_line(stage, user_controls_treble, start_time - self.delay,
                                           number_of_user_controlled_bells)
