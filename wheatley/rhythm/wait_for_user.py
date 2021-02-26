""" A module for the Rhythm decorator class that adds the ability to wait for human ringers. """

import logging

from typing import Any, Dict, Set

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

        self._expected_bells: Dict[Stroke, Set] = {HANDSTROKE: set(), BACKSTROKE: set()}
        self._early_bells: Dict[Stroke, Set] = {HANDSTROKE: set(), BACKSTROKE: set()}

        self.delay = 0.0

        self.logger = logging.getLogger(self.logger_name)

        self._should_return_to_mainloop = False

    def return_to_mainloop(self) -> None:
        """
        When called, this function requires that Wheatley's main thread should return from
        wait_for_bell_time and give control back to the mainloop within a reasonable amount of time
        (i.e. 1/10 of a second is acceptable, but anything approacing a second is not)
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
            self.logger.debug(f"Waiting for {bell}...")
            while bell in self._expected_bells[stroke]:
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

    def expect_bell(self, expected_bell: Bell, row_number: int, place: int, expected_stroke: Stroke) -> None:
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
            self._early_bells[expected_stroke.opposite()].clear()

        if expected_bell not in self._early_bells[expected_stroke]:
            self._expected_bells[expected_stroke].add(expected_bell)

    def change_setting(self, key: str, value: Any, real_time: float) -> None:
        # Keep lying to _inner_rhythm about what the current time is
        self._inner_rhythm.change_setting(key, value, real_time - self.delay)

    def on_bell_ring(self, bell: Bell, stroke: Stroke, real_time: float) -> None:
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
                self.logger.debug(f"{bell} rung at {stroke}")

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
        self._expected_bells[HANDSTROKE].clear()
        self._expected_bells[BACKSTROKE].clear()

        self._early_bells[HANDSTROKE].clear()
        self._early_bells[BACKSTROKE].clear()

        self._current_stroke = HANDSTROKE

        # Clear any current waiting loops
        self.sleep(2 * self.sleep_time)

        self._inner_rhythm.initialise_line(stage, user_controls_treble, start_time - self.delay,
                                           number_of_user_controlled_bells)
