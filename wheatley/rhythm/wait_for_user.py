""" A module to contain the Rhythm type which waits for a user to ring. """

import logging
from wheatley.tower import HANDSTROKE, BACKSTROKE, stroke_to_string
from .abstract_rhythm import Rhythm

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

            if delay_for_user:
                self.delay += delay_for_user
                self.logger.info(f"Delayed for {delay_for_user}")

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
