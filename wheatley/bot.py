"""
Module to contain the Bot class, which acts as 'glue' to combine the rhythm, row generation and
socket-io communication provided by the Rhythm, RowGenerator and Tower objects into a useful
program.
"""

import time

from wheatley import calls
from wheatley.row_generation import RowGenerator
from wheatley.bell import Bell
from wheatley.rhythm import Rhythm
from wheatley.tower import RingingRoomTower


class Bot:
    """
    A class to hold all the information that the bot will use to glue together the rhythm,
    row_gen and socket-io parts together into a useful program.
    """

    def __init__(self, tower: RingingRoomTower, row_generator: RowGenerator, do_up_down_in,
                 stop_at_rounds, rhythm: Rhythm):
        """ Initialise a Bot with all the parts it needs to run. """

        self._rhythm = rhythm

        self._do_up_down_in = do_up_down_in
        self._stop_at_rounds = stop_at_rounds

        self.row_generator = row_generator

        self._tower = tower

        self._tower.invoke_on_call[calls.LOOK_TO].append(self._on_look_to)
        self._tower.invoke_on_call[calls.GO].append(self._on_go)
        self._tower.invoke_on_call[calls.BOB].append(self._on_bob)
        self._tower.invoke_on_call[calls.SINGLE].append(self._on_single)
        self._tower.invoke_on_call[calls.THATS_ALL].append(self._on_thats_all)
        self._tower.invoke_on_call[calls.STAND].append(self._on_stand_next)

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
        """
        Returns true if the current row (determined by self._row_number) represents a handstroke.
        """

        return self._row_number % 2 == 0

    @property
    def stage(self):
        """ Convenient property to find the number of bells in the current tower. """

        return self._tower.number_of_bells

    # Callbacks
    def _on_look_to(self):
        """ Callback called when a user calls 'Look To'. """

        treble = Bell.from_number(1)

        # Count number of user controlled bells
        number_of_user_controlled_bells = 0
        for i in range(self.stage):
            if self._tower.user_controlled(Bell.from_index(i)):
                number_of_user_controlled_bells += 1

        self._rhythm.initialise_line(self.stage, self._tower.user_controlled(treble),
                                     time.time() + 3, number_of_user_controlled_bells)

        # Clear all the flags
        self._should_stand = False
        self._should_start_method = False
        self._should_start_ringing_rounds = False

        # Reset the state, so that the bot starts by ringing rounds
        self._is_ringing = True
        self._is_ringing_rounds = True

        # Start at the first place of the first row
        self._row_number = 0
        self._place = 0

        self.start_next_row()

    def _on_go(self):
        """ Callback called when a user calls 'Go'. """

        if self._is_ringing_rounds:
            self._should_start_method = True

    def _on_bob(self):
        """ Callback called when a user calls 'Bob'. """

        self.row_generator.set_bob()

    def _on_single(self):
        """ Callback called when a user calls 'Single'. """

        self.row_generator.set_single()

    def _on_thats_all(self):
        """ Callback called when a user calls 'That`s All'. """

        self._should_start_ringing_rounds = True

    def _on_stand_next(self):
        """ Callback called when a user calls 'Stand Next'. """

        self._should_stand = True

    def _on_bell_ring(self, bell, stroke):
        """ Callback called when the Tower recieves a signal that a bell has been rung. """

        if self._tower.user_controlled(bell):
            # This will give us the stroke _after_ the bell rings, we have to invert it, because
            # otherwise this will always expect the bells on the wrong stroke and no ringing will
            # ever happen
            self._rhythm.on_bell_ring(bell, not stroke, time.time())

    # Mainloop and helper methods
    def expect_bell(self, index, bell):
        """ Called to let the rhythm expect a user-controlled bell at a certain time and stroke. """

        if self._tower.user_controlled(bell):
            self._rhythm.expect_bell(
                bell,
                self._row_number,
                index,
                self.is_handstroke
            )

    def start_next_row(self):
        """
        Creates a new row from the row generator and tells the rhythm to expect the new bells.
        """

        if self._is_ringing_rounds:
            for index in range(self.stage):
                self.expect_bell(index, Bell.from_index(index))
        else:
            self._row = self.row_generator.next_row(self.is_handstroke)

            for (index, bell) in enumerate(self._row):
                self.expect_bell(index, bell)

    def start_method(self):
        """
        Called when the ringing is about to go into changes.
        Resets the row_generator and starts the next row.
        """

        assert self.row_generator.number_of_bells == self._tower.number_of_bells, \
            f"{self.row_generator.number_of_bells} != {self._tower.number_of_bells}"
        self.row_generator.reset()
        self.start_next_row()

    def tick(self):
        """ Called every time the main loop is executed when the bot is ringing. """

        bell = Bell.from_index(self._place) if self._is_ringing_rounds else self._row[self._place]

        user_controlled = self._tower.user_controlled(bell)
        self._rhythm.wait_for_bell_time(time.time(), bell, self._row_number, self._place,
                                        user_controlled, self.is_handstroke)
        if not user_controlled:
            self._tower.ring_bell(bell, self.is_handstroke)

        self._place += 1

        if self._place == self.stage:
            # Determine if we're finishing a handstroke
            has_just_rung_rounds = True

            if self._row is None:
                has_just_rung_rounds = False
            else:
                for i, bell in enumerate(self._row):
                    if bell.index != i:
                        has_just_rung_rounds = False

            # Generate the next row and update row indices
            self._row_number += 1
            self._place = 0
            self.start_next_row()

            # Implement handbell-style 'up down in'
            if self._do_up_down_in:
                if self._is_ringing_rounds and self._row_number == 2:
                    self._should_start_method = True

            # Implement handbell-style stopping at rounds
            if self._stop_at_rounds:
                if has_just_rung_rounds:
                    self._should_stand = False
                    self._is_ringing = False

            # If we're starting a handstroke, we should convert all the flags into actions
            if self._row_number % 2 == 0:
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

    def main_loop(self):
        """
        The main_loop of the bot.
        The main thread will get stuck forever in this function whilst the bot rings.
        """

        while True:
            if self._is_ringing:
                self.tick()

            time.sleep(0.01)
