import time
import unittest
from threading import Thread

from unittest.mock import Mock

from wheatley.stroke import HANDSTROKE, BACKSTROKE
from wheatley.bell import Bell
from wheatley.rhythm import Rhythm, WaitForUserRhythm

treble = Bell.from_number(1)
second = Bell.from_number(2)


class WaitForUserRhythmTests(unittest.TestCase):
    def setUp(self):
        self.mock_inner_rhythm = Mock(spec=Rhythm)
        self.wait_rhythm = WaitForUserRhythm(self.mock_inner_rhythm)
        self.wait_rhythm.sleep = self._patched_sleep

        self.waiting_for_bell_time = False

        self._finished_test = False
        self._sleeping = False
        self._return_from_sleep = False
        self.total_sleep_calls = 0
        self.total_sleep_delay = 0

    def tearDown(self):
        self._finished_test = True

    def _patched_sleep(self, seconds):
        """ Replacement sleep function that loops until advance_patched_sleep() is called
        Allows controlling how many times sleep() returns.
        """
        self._sleeping = True
        self.total_sleep_calls += 1
        self.total_sleep_delay += seconds
        while not self._return_from_sleep and not self._finished_test:
            time.sleep(0.001)
        self._return_from_sleep = False
        self._sleeping = False

    def advance_patched_sleep(self, seconds: float = 0.01):
        """ Makes _patched_sleep() return
        Allows controlling how many times sleep() returns.
        """
        expected_sleeps = seconds / WaitForUserRhythm.sleep_time
        for _ in range(round(expected_sleeps)):
            while not self._sleeping or self._return_from_sleep:
                time.sleep(0.001)
            self._return_from_sleep = True

    def start_wait_for_bell_time_thread(self, current_time, bell, row_number, place, user_controlled, stroke):
        """ Runs wait_for_bell_time() on a different thread, as it should loop until on_bell_ring() is called
        """

        def _wait_for_bell_time():
            self.waiting_for_bell_time = True
            self.wait_rhythm.wait_for_bell_time(current_time, bell, row_number, place, user_controlled,
                                                stroke)
            self.waiting_for_bell_time = False

        wait_thread = Thread(name=f"wait_for_bell_time_{bell}", target=_wait_for_bell_time)
        wait_thread.start()

    def assert_not_waiting_for_bell_time(self):
        count = 0
        # Return from a last sleep just in case
        self._return_from_sleep = True
        time.sleep(0.01)

        while self.waiting_for_bell_time and count < 50:
            time.sleep(0.001)
            count += 1
        self.assertFalse(self.waiting_for_bell_time, "Waiting for bell to ring")
        self._return_from_sleep = False

    def test_on_bell_ring__no_initial_delay(self):
        self.wait_rhythm.expect_bell(treble, 1, 1, HANDSTROKE)

        self.wait_rhythm.on_bell_ring(treble, HANDSTROKE, 0.5)

        self.mock_inner_rhythm.on_bell_ring.assert_called_once_with(treble, HANDSTROKE, 0.5)

    def test_on_bell_ring__subtracts_existing_delay(self):
        self.wait_rhythm.expect_bell(treble, 1, 1, HANDSTROKE)
        self.wait_rhythm.delay = 10

        self.wait_rhythm.on_bell_ring(treble, HANDSTROKE, 10.5)

        self.mock_inner_rhythm.on_bell_ring.assert_called_once_with(treble, HANDSTROKE, 0.5)

    def test_on_bell_ring__uses_original_delay_while_waiting(self):
        # Arrange
        initial_delay = 10
        expected_time = 11
        actual_time = 11.1

        self.wait_rhythm.expect_bell(treble, 1, 1, HANDSTROKE)
        self.wait_rhythm.delay = initial_delay

        # Start waiting for treble
        self.start_wait_for_bell_time_thread(current_time=expected_time, bell=treble, row_number=1, place=1,
                                             user_controlled=True, stroke=HANDSTROKE)

        self.advance_patched_sleep(seconds=actual_time - expected_time)

        # Treble rung by user
        self.wait_rhythm.on_bell_ring(treble, HANDSTROKE, actual_time)
        self.assert_not_waiting_for_bell_time()

        # 11.1 - 10 = 1.1
        self.mock_inner_rhythm.on_bell_ring.assert_called_once_with(treble, HANDSTROKE,
                                                                    actual_time - initial_delay)
        # 10 + (11.1 - 11) = 10.1
        self.assertEqual(10.1, round(self.wait_rhythm.delay, 2))

    def test_wait_for_bell_time__bell_rung_early_doesnt_wait(self):
        # Arrange
        initial_delay = 10
        expected_time = 11
        actual_time = 10.5

        self.wait_rhythm.delay = initial_delay
        self.wait_rhythm.expect_bell(treble, 1, 1, HANDSTROKE)

        # Treble rung by user
        self.wait_rhythm.on_bell_ring(treble, HANDSTROKE, actual_time)

        # Start waiting for treble
        self.start_wait_for_bell_time_thread(current_time=expected_time, bell=treble, row_number=1, place=1,
                                             user_controlled=True, stroke=HANDSTROKE)

        # Returns immediately without waiting
        self.assert_not_waiting_for_bell_time()

        self.mock_inner_rhythm.on_bell_ring.assert_called_once_with(treble, HANDSTROKE,
                                                                    actual_time - initial_delay)
        self.assertEqual(initial_delay, self.wait_rhythm.delay)

    def test_wait_for_bell_time__bell_rung_early_in_row_doesnt_wait(self):
        # Arrange
        initial_delay = 0
        expected_first_bell_time = 1
        expected_second_bell_time = 2

        self.wait_rhythm.expect_bell(treble, 1, 1, HANDSTROKE)
        self.wait_rhythm.expect_bell(second, 1, 2, HANDSTROKE)
        self.wait_rhythm.delay = initial_delay

        # Start waiting for treble
        self.start_wait_for_bell_time_thread(current_time=expected_first_bell_time, bell=treble, row_number=1,
                                             place=1, user_controlled=True, stroke=HANDSTROKE)

        self.advance_patched_sleep(seconds=0.05)

        # Second rung early by user
        self.wait_rhythm.on_bell_ring(second, HANDSTROKE, 1.05)

        self.advance_patched_sleep(seconds=0.05)
        self.assertTrue(self.waiting_for_bell_time)

        # Treble rung by user
        self.wait_rhythm.on_bell_ring(treble, HANDSTROKE, 1.1)
        self.assert_not_waiting_for_bell_time()

        # Start waiting for second
        self.start_wait_for_bell_time_thread(current_time=expected_second_bell_time, bell=second,
                                             row_number=1, place=1, user_controlled=True, stroke=HANDSTROKE)
        # Returns immediately without waiting
        self.assert_not_waiting_for_bell_time()

        self.mock_inner_rhythm.on_bell_ring.assert_any_call(second, HANDSTROKE, 1.05)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, HANDSTROKE, 1.1)
        # 1.1 - 1, Second being early has not added delay
        self.assertEqual(0.1, round(self.wait_rhythm.delay, 2))

    def test_wait_for_bell_time__bell_rung_early_in_previous_row_doesnt_wait(self):
        # Arrange
        initial_delay = 0
        expected_first_time = 1
        expected_second_time = 2

        self.wait_rhythm.expect_bell(treble, 1, 1, HANDSTROKE)
        self.wait_rhythm.delay = initial_delay

        # Treble rung by user twice, so is now on wrong stroke
        self.wait_rhythm.on_bell_ring(treble, HANDSTROKE, 1)
        self.wait_rhythm.on_bell_ring(treble, BACKSTROKE, 1.1)

        self.start_wait_for_bell_time_thread(current_time=expected_first_time, bell=treble, row_number=1,
                                             place=1, user_controlled=True, stroke=HANDSTROKE)
        self.assert_not_waiting_for_bell_time()

        # Next row, treble is already rung BACKSTROKE
        self.wait_rhythm.expect_bell(treble, 2, 1, BACKSTROKE)

        self.start_wait_for_bell_time_thread(current_time=expected_second_time, bell=treble, row_number=2,
                                             place=1, user_controlled=True, stroke=BACKSTROKE)

        self.assert_not_waiting_for_bell_time()

        self.assertEqual(0, self.wait_rhythm.delay)

        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, HANDSTROKE, 1)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, BACKSTROKE, 1.1)

    def test_wait_for_bell_time__bell_early_and_corrected_in_previous_row_waits_for_bell(self):
        # Arrange
        expected_first_time = 1
        expected_second_time = 2

        self.wait_rhythm.expect_bell(treble, 1, 1, HANDSTROKE)

        # Treble rung by user
        self.wait_rhythm.on_bell_ring(treble, HANDSTROKE, 1)

        self.start_wait_for_bell_time_thread(current_time=expected_first_time, bell=treble, row_number=1,
                                             place=1, user_controlled=True, stroke=HANDSTROKE)

        # Treble accidentally rung by user and corrected back to the right stroke
        self.wait_rhythm.on_bell_ring(treble, BACKSTROKE, 1.1)
        self.wait_rhythm.on_bell_ring(treble, HANDSTROKE, 1.2)

        self.assert_not_waiting_for_bell_time()

        self.wait_rhythm.expect_bell(treble, 2, 1, BACKSTROKE)

        self.start_wait_for_bell_time_thread(current_time=expected_second_time, bell=treble, row_number=2,
                                             place=1, user_controlled=True, stroke=BACKSTROKE)

        self.assertTrue(self.waiting_for_bell_time)

        self.wait_rhythm.on_bell_ring(treble, BACKSTROKE, expected_second_time)

        self.assertEqual(0, self.wait_rhythm.delay)

        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, HANDSTROKE, 1)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, BACKSTROKE, 1.1)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, HANDSTROKE, 1.2)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, BACKSTROKE, expected_second_time)


if __name__ == '__main__':
    unittest.main()
