""" A module to hold the abstract Rhythm class used to specify what features a 'Rhythm' must have. """

import time

from abc import ABCMeta, abstractmethod

from wheatley.bell import Bell

class Rhythm(metaclass=ABCMeta):
    """
    An abstract Rhythm class, used as an interface by the Bot class to interact with Rhythms.
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
