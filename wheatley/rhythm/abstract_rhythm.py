""" Module for the base Rhythm class, from which all other Rhythm classes inherit. """

import time

from abc import ABCMeta, abstractmethod
from typing import Any

from wheatley.stroke import Stroke
from wheatley.bell import Bell


class Rhythm(metaclass=ABCMeta):
    """
    An abstract Rhythm class, used as an interface by the Bot class to interact with Rhythms.
    """

    @abstractmethod
    def return_to_mainloop(self) -> None:
        """
        When called, this function requires that Wheatley's main thread should return from
        wait_for_bell_time and give control back to the mainloop within a reasonable amount of time
        (i.e. 1/10 of a second is acceptable, but anything approacing a second is not)
        """

    @abstractmethod
    def wait_for_bell_time(self, current_time: float, bell: Bell, row_number: int, place: int,
                           user_controlled: bool, stroke: Stroke) -> None:
        """ Sleeps the thread until a given Bell should have rung. """

    @abstractmethod
    def expect_bell(self, expected_bell: Bell, row_number: int, place: int, expected_stroke: Stroke) -> None:
        """
        Indicates that a given Bell is expected to be rung at a given row, place and stroke.
        Used by the rhythm so that when that bell is rung later, it can tell where that bell
        _should_ have been in the ringing, and so can use that knowledge to inform the speed of the
        ringing.
        """

    @abstractmethod
    def change_setting(self, key: str, value: Any, real_time: float) -> None:
        """ Called when the Ringing Room server asks Wheatley to change a setting. """
        # We need the `real_time` param because `WaitForUserRhythm` lies to its inner rhythm about
        # the real time (in order to hold up over people without killing the regression), and
        # `RegressionRhythm` needs the current 'time' so that it can update its line accurately when
        # the peal speed is changed.

    @abstractmethod
    def on_bell_ring(self, bell: Bell, stroke: Stroke, real_time: float) -> None:
        """
        Called when a bell is rung at a given stroke.  Used as a callback from the Tower class.
        """

    @abstractmethod
    def initialise_line(self, stage: int, user_controls_treble: bool, start_time: float,
                        number_of_user_controlled_bells: int) -> None:
        """ Allow the Rhythm object to initialise itself when 'Look to' is called. """

    def sleep(self, seconds: float) -> None: #  pylint: disable=no-self-use
        """ Sleeps for given number of seconds. Allows mocking in tests"""
        time.sleep(seconds)
