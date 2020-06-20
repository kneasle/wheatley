import time

from rhythm import Rhythm

class Bot:
    def __init__ (self, tower, row_generator, do_up_down_in = True):
        self._rhythm = Rhythm (self)

        self.do_up_down_in = do_up_down_in

        self.row_generator = row_generator

        self._tower = tower

        self._tower.on_thats_all = self._on_thats_all
        self._tower.on_go = self._on_go
        self._tower.on_stand_next = self._on_stand_next
        self._tower.on_look_to = self._on_look_to
        self._tower.on_bell_ring = self._on_bell_ring

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
    def is_handstroke (self):
        return self._row_number % 2 == 0

    @property
    def stage (self):
        return self._tower.number_of_bells



    # Callbacks
    def _on_look_to (self):
        self._rhythm.initialise_line (time.time () + 3)

        self._should_stand = False
        self._should_start_method = False
        self._should_start_ringing_rounds = False

        self._is_ringing = True
        self._is_ringing_rounds = True

        self._row_number = 0
        self._place = 0

        # Expect the bells in rounds
        for b in range (self.stage):
            self.expect_bell (b, b)

    def _on_go (self):
        if self._is_ringing_rounds:
            self._should_start_method = True

    def _on_thats_all (self):
        self._should_start_ringing_rounds = True

    def _on_stand_next (self):
        self._should_stand = True

    def _on_bell_ring (self, bell, stroke):
        if self._tower.user_controlled (bell):
            # This will give us the stroke _after_ the bell rings, we have to invert it, because 
            # otherwise this will always expect the bells on the wrong stroke
            self._rhythm.on_bell_ring (bell, not stroke, time.time ())

    # Mainloop and helper methods
    def expect_bell (self, index, bell):
        if self._tower.user_controlled (bell):
            self._rhythm.expect_bell (
                bell,
                self._rhythm.index_to_blow_time (self._row_number, index),
                self.is_handstroke
            )

    def start_next_row (self):
        self._row = [x - 1 for x in self.row_generator.next_row (self.is_handstroke)]

        for (index, bell) in enumerate (self._row):
            self.expect_bell (index, bell)

    def start_method (self):
        self.row_generator.reset ()
        self.start_next_row ()

    def main_loop (self):
        while True:
            if self._is_ringing:
                if time.time () > self._rhythm.index_to_real_time (self._row_number, self._place):
                    bell = self._place if self._is_ringing_rounds else self._row [self._place]

                    if not self._tower.user_controlled (bell):
                        self._tower.ring_bell (bell, self.is_handstroke)

                    self._place += 1

                    if self._place == self.stage:
                        self._row_number += 1
                        self._place = 0

                        if not self._is_ringing_rounds:
                            self.start_next_row ()
                        else:
                            for b in range (self.stage):
                                self.expect_bell (b, b)

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

                                self.start_method ()

                            if self._should_start_ringing_rounds and not self._is_ringing_rounds:
                                self._should_start_ringing_rounds = False
                                self._is_ringing_rounds = True

            time.sleep (0.01)
