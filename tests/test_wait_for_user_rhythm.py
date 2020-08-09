import time
import unittest
from threading import Thread

from unittest.mock import Mock

from wheatley.bell import Bell
from wheatley.rhythm import Rhythm, WaitForUserRhythm

treble = Bell.from_number(1)
second = Bell.from_number(2)

handstroke = True
backstroke = False


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
        self._sleeping = True
        self.total_sleep_calls += 1
        self.total_sleep_delay += seconds
        while not self._return_from_sleep and not self._finished_test:
            time.sleep(0.001)
        self._return_from_sleep = False
        self._sleeping = False

    def return_from_sleep(self, seconds: float = 0.01, wait_for_sleep=True):
        expected_sleeps = seconds / WaitForUserRhythm.sleep_time
        for _ in range(round(expected_sleeps)):
            while wait_for_sleep and not self._sleeping or self._return_from_sleep:
                time.sleep(0.001)
            self._return_from_sleep = True

    def start_wait_for_bell_time(self, current_time, bell, row_number, place, user_controlled, stroke):
        # Run on a different thread as it will loop until on_bell_ring called.
        def _wait_for_bell_time():
            self.waiting_for_bell_time = True
            self.wait_rhythm.wait_for_bell_time(current_time, bell, row_number, place, user_controlled, stroke)
            self.waiting_for_bell_time = False

        wait_thread = Thread(name="wait_for_bell_time", target=_wait_for_bell_time)
        wait_thread.start()

    def assert_not_waiting_for_bell_time(self):
        count = 0
        time.sleep(0.01)

        while self.waiting_for_bell_time and count < 100:
            time.sleep(0.001)
            count += 1
        self.assertFalse(self.waiting_for_bell_time, "Waiting for bell to ring")

    def test_on_bell_ring__no_initial_delay(self):
        self.wait_rhythm.expect_bell(treble, 1, 1, handstroke)

        self.wait_rhythm.on_bell_ring(treble, handstroke, 0.5)

        self.mock_inner_rhythm.on_bell_ring.assert_called_once_with(treble, handstroke, 0.5)

    def test_on_bell_ring__subtracts_existing_delay(self):
        self.wait_rhythm.expect_bell(treble, 1, 1, handstroke)
        self.wait_rhythm.delay = 10

        self.wait_rhythm.on_bell_ring(treble, handstroke, 10.5)

        self.mock_inner_rhythm.on_bell_ring.assert_called_once_with(treble, handstroke, 0.5)

    def test_on_bell_ring__uses_original_delay_while_waiting(self):
        initial_delay = 10
        expected_time = 11
        actual_time = 11.1

        self.wait_rhythm.expect_bell(treble, 1, 1, handstroke)
        self.wait_rhythm.delay = initial_delay

        self.start_wait_for_bell_time(current_time=expected_time, bell=treble, row_number=1, place=1,
                                      user_controlled=True, stroke=handstroke)

        self.return_from_sleep(seconds=actual_time - expected_time)

        self.wait_rhythm.on_bell_ring(treble, handstroke, actual_time)
        self.return_from_sleep(wait_for_sleep=False)
        self.assert_not_waiting_for_bell_time()

        # 11.1 - 10 = 1.1
        self.mock_inner_rhythm.on_bell_ring.assert_called_once_with(treble, handstroke, actual_time - initial_delay)
        # 10 + (11.1 - 11) = 10.1
        self.assertEqual(10.1, round(self.wait_rhythm.delay, 2))

    def test_wait_for_bell_time__bell_rung_early_in_row_doesnt_wait(self):
        initial_delay = 0
        expected_first_bell_time = 1
        expected_second_bell_time = 2

        self.wait_rhythm.expect_bell(treble, 1, 1, handstroke)
        self.wait_rhythm.expect_bell(second, 1, 2, handstroke)
        self.wait_rhythm.delay = initial_delay

        self.start_wait_for_bell_time(current_time=expected_first_bell_time, bell=treble, row_number=1, place=1,
                                      user_controlled=True, stroke=handstroke)

        self.return_from_sleep(seconds=0.1)

        self.wait_rhythm.on_bell_ring(second, handstroke, 1.1)

        self.return_from_sleep(seconds=0.1)
        self.assertTrue(self.waiting_for_bell_time)
        self.wait_rhythm.on_bell_ring(treble, handstroke, 1.2)
        self.return_from_sleep(wait_for_sleep=False)
        self.assert_not_waiting_for_bell_time()
        self.start_wait_for_bell_time(current_time=expected_second_bell_time, bell=second, row_number=1, place=1,
                                      user_controlled=True, stroke=handstroke)
        self.assert_not_waiting_for_bell_time()

        self.mock_inner_rhythm.on_bell_ring.assert_any_call(second, handstroke, 1.1)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, handstroke, 1.2)
        # 1.2 - 1, Second being early has not added delay
        self.assertEqual(0.2, round(self.wait_rhythm.delay, 2))

    def test_wait_for_bell_time__bell_rung_early_in_previous_row_doesnt_wait(self):
        initial_delay = 0
        expected_first_time = 1
        expected_second_time = 2

        self.wait_rhythm.expect_bell(treble, 1, 1, handstroke)
        self.wait_rhythm.delay = initial_delay

        self.wait_rhythm.on_bell_ring(treble, handstroke, 1)

        self.start_wait_for_bell_time(current_time=expected_first_time, bell=treble, row_number=1, place=1,
                                      user_controlled=True, stroke=handstroke)

        self.wait_rhythm.on_bell_ring(treble, backstroke, 1.1)

        self.return_from_sleep(wait_for_sleep=False)
        self.assert_not_waiting_for_bell_time()

        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, handstroke, 1)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, backstroke, 1.1)

        self.wait_rhythm.expect_bell(treble, 2, 1, backstroke)

        self.start_wait_for_bell_time(current_time=expected_second_time, bell=treble, row_number=2, place=1,
                                      user_controlled=True, stroke=backstroke)

        self.assert_not_waiting_for_bell_time()

        self.assertEqual(0, self.wait_rhythm.delay)

    def test_wait_for_bell_time__bell_early_and_corrected_in_previous_row_waits_for_bell(self):
        expected_first_time = 1
        expected_second_time = 2

        self.wait_rhythm.expect_bell(treble, 1, 1, handstroke)

        self.wait_rhythm.on_bell_ring(treble, handstroke, 1)

        self.start_wait_for_bell_time(current_time=expected_first_time, bell=treble, row_number=1, place=1,
                                      user_controlled=True, stroke=handstroke)

        self.wait_rhythm.on_bell_ring(treble, backstroke, 1.1)
        self.wait_rhythm.on_bell_ring(treble, handstroke, 1.2)

        self.return_from_sleep(wait_for_sleep=False)
        self.assert_not_waiting_for_bell_time()

        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, handstroke, 1)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, backstroke, 1.1)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, handstroke, 1.2)

        self.wait_rhythm.expect_bell(treble, 2, 1, backstroke)

        self.start_wait_for_bell_time(current_time=expected_second_time, bell=treble, row_number=2, place=1,
                                      user_controlled=True, stroke=backstroke)

        self.assertTrue(self.waiting_for_bell_time)

        self.wait_rhythm.on_bell_ring(treble, backstroke, expected_second_time)
        self.mock_inner_rhythm.on_bell_ring.assert_any_call(treble, backstroke, expected_second_time)

        self.assertEqual(0, self.wait_rhythm.delay)


if __name__ == '__main__':
    unittest.main()
