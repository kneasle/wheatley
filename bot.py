import time
from typing import Optional

from Calls import Calls
from RowGeneration.RowGenerator import RowGenerator
from bell import Bell
from rhythm import RegressionRhythm, Rhythm
from tower import RingingRoomTower


class Bot:
    def __init__(self, tower: RingingRoomTower, row_generator: RowGenerator, do_up_down_in=True,
                 rhythm: Optional[Rhythm] = None):
        self._rhythm = rhythm or RegressionRhythm()

        self.do_up_down_in = do_up_down_in

        self.row_generator = row_generator

        self._tower = tower

        self._tower.invoke_on_call[Calls.LookTo].append(self._on_look_to)
        self._tower.invoke_on_call[Calls.Go].append(self._on_go)
        self._tower.invoke_on_call[Calls.Bob].append(self._on_bob)
        self._tower.invoke_on_call[Calls.Single].append(self._on_single)
        self._tower.invoke_on_call[Calls.ThatsAll].append(self._on_thats_all)
        self._tower.invoke_on_call[Calls.Stand].append(self._on_stand_next)

        self._tower.invoke_on_bell_rung.append(self._on_bell_ring)

        self._is_ringing = False
        self._is_ringing_rounds = True

        self._should_start_method = False
        self._should_start_ringing_rounds = False
        self._should_stand = False

        self._row_number = 0
        self._place = 0

        self._row = None

    # Convenient properties that are frequently used
    @property
    def is_handstroke(self):
        return self._row_number % 2 == 0

    @property
    def stage(self):
        return self._tower.number_of_bells

    # Callbacks
    def _on_look_to(self):
        treble = Bell.from_number(1)
        self._rhythm.initialise_line(self.stage, self._tower.user_controlled(treble), time.time() + 3)

        self._should_stand = False
        self._should_start_method = False
        self._should_start_ringing_rounds = False

        self._is_ringing = True
        self._is_ringing_rounds = True

        self._row_number = 0
        self._place = 0

        # Expect the bells in rounds
        for b in range(self.stage):
            self.expect_bell(b, Bell.from_index(b))

    def _on_go(self):
        if self._is_ringing_rounds:
            self._should_start_method = True

    def _on_bob(self):
        self.row_generator.set_bob()

    def _on_single(self):
        self.row_generator.set_single()

    def _on_thats_all(self):
        self._should_start_ringing_rounds = True

    def _on_stand_next(self):
        self._should_stand = True

    def _on_bell_ring(self, bell, stroke):
        if self._tower.user_controlled(bell):
            # This will give us the stroke _after_ the bell rings, we have to invert it, because 
            # otherwise this will always expect the bells on the wrong stroke
            self._rhythm.on_bell_ring(bell, not stroke, time.time())

    # Mainloop and helper methods
    def expect_bell(self, index, bell):
        if self._tower.user_controlled(bell):
            self._rhythm.expect_bell(
                bell,
                self._row_number,
                index,
                self.is_handstroke
            )

    def start_next_row(self):
        self._row = self.row_generator.next_row(self.is_handstroke)

        for (index, bell) in enumerate(self._row):
            self.expect_bell(index, bell)

    def start_method(self):
        assert self.row_generator.number_of_bells == self._tower.number_of_bells, \
            f"{self.row_generator.number_of_bells} != {self._tower.number_of_bells}"
        self.row_generator.reset()
        self.start_next_row()

    def main_loop(self):
        while True:
            if self._is_ringing:
                bell = Bell.from_index(self._place) if self._is_ringing_rounds else self._row[self._place]

                user_controlled = self._tower.user_controlled(bell)
                self._rhythm.wait_for_bell_time(time.time(), bell, self._row_number, self._place, user_controlled,
                                                self.is_handstroke)
                if not user_controlled:
                    self._tower.ring_bell(bell, self.is_handstroke)

                self._place += 1

                if self._place == self.stage:
                    self._row_number += 1
                    self._place = 0

                    if self._is_ringing_rounds:
                        for b in range(self.stage):
                            self.expect_bell(b, Bell.from_index(b))
                    else:
                        self.start_next_row()

                    if self._is_ringing_rounds:
                        if self._row_number == 2 and self.do_up_down_in:
                            self._should_start_method = True

                    if self._row_number % 2 == 0:
                        # We're just starting a handstroke
                        if self._should_stand:
                            self._should_stand = False
                            self._is_ringing = False

                        if self._should_start_method and self._is_ringing_rounds:
                            self._should_start_method = False
                            self._is_ringing_rounds = False

                            self.start_method()

                        if self._should_start_ringing_rounds and not self._is_ringing_rounds:
                            self._should_start_ringing_rounds = False
                            self._is_ringing_rounds = True

            time.sleep(0.01)
