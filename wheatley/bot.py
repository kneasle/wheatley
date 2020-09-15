"""
Module to contain the Bot class, which acts as 'glue' to combine the rhythm, row generation and
socket-io communication provided by the Rhythm, RowGenerator and Tower objects into a useful
program.
"""

import time
import logging
from typing import Optional

from wheatley import calls
from wheatley.row_generation import RowGenerator
from wheatley.bell import Bell
from wheatley.rhythm import Rhythm
from wheatley.tower import RingingRoomTower
from wheatley.parsing import to_bool, json_to_row_generator, RowGenParseError


# Number of seconds that Wheatley is not ringing before Wheatley will return from the mainloop
# Only applies when Wheatley is running in server mode
INACTIVITY_EXIT_TIME = 300


class Bot:
    """
    A class to hold all the information that the bot will use to glue together the rhythm,
    row_gen and socket-io parts together into a useful program.
    """

    logger_name = "BOT"

    def __init__(self, tower: RingingRoomTower, row_generator: RowGenerator, do_up_down_in: bool,
                 stop_at_rounds: bool, rhythm: Rhythm, user_name: Optional[str] = None, server_mode = False):
        """ Initialise a Bot with all the parts it needs to run. """
        self._server_mode = server_mode
        self._last_activity_time = time.time()

        self._rhythm = rhythm
        self._do_up_down_in = do_up_down_in
        self._stop_at_rounds = stop_at_rounds
        self._user_name = user_name

        self.row_generator = row_generator
        # This is the row generator that will be used after 'Look to' is called for the next time, allowing
        # for changing the method or composition whilst Wheatley is running.
        self.next_row_generator = None

        self._tower = tower

        self._tower.invoke_on_call[calls.LOOK_TO].append(self._on_look_to)
        self._tower.invoke_on_call[calls.GO].append(self._on_go)
        self._tower.invoke_on_call[calls.BOB].append(self._on_bob)
        self._tower.invoke_on_call[calls.SINGLE].append(self._on_single)
        self._tower.invoke_on_call[calls.THATS_ALL].append(self._on_thats_all)
        self._tower.invoke_on_call[calls.STAND].append(self._on_stand_next)
        self._tower.invoke_on_bell_rung.append(self._on_bell_ring)
        self._tower.invoke_on_reset.append(self._on_size_change)
        if self._server_mode:
            self._tower.invoke_on_setting_change.append(self._on_setting_change)
            self._tower.invoke_on_row_gen_change.append(self._on_row_gen_change)
            self._tower.invoke_on_stop_touch.append(self._on_stop_touch)

        self._is_ringing = False
        self._is_ringing_rounds = True
        self._should_start_method = False
        self._should_start_ringing_rounds = False
        self._should_stand = False

        self._row_number = 0
        self._place = 0
        self._row = None

        self.logger = logging.getLogger(self.logger_name)

    # Convenient properties that are frequently used
    @property
    def is_handstroke(self):
        """ Returns true if the current row (determined by self._row_number) represents a handstroke. """
        return self._row_number % 2 == 0

    @property
    def stage(self):
        """ Convenient property to find the number of bells in the current tower. """
        return self._tower.number_of_bells

    # Callbacks
    def _on_setting_change(self, key, value):
        def log_invalid_key(message):
            self.logger.warning(f"Invalid value for {key}: {message}")

        if key == 'use_up_down_in':
            try:
                self._do_up_down_in = to_bool(value)
                self.logger.info(f"Setting 'use_up_down_in' to {self._do_up_down_in}")
            except ValueError:
                log_invalid_key(f"{value} cannot be converted into a bool")
        elif key == 'stop_at_rounds':
            try:
                self._stop_at_rounds = to_bool(value)
                self.logger.info(f"Setting 'stop_at_rounds' to {value}")
            except ValueError:
                log_invalid_key(f"{value} cannot be converted into a bool")
        else:
            self._rhythm.change_setting(key, value)

    def _on_row_gen_change(self, row_gen_json):
        try:
            self.next_row_generator = json_to_row_generator(row_gen_json, self.logger)

            self.logger.info("Successfully updated next row gen")
        except RowGenParseError as e:
            self.logger.warning(e)

    def _on_size_change(self):
        if not self.row_generator.is_tower_size_valid(self._tower.number_of_bells):
            self.logger.warning(f"Row generation requires {self.row_generator.number_of_bells} \
bells, but the current tower has {self._tower.number_of_bells}.  Wheatley will crash when you go \
into changes unless something is done!")

    def _on_look_to(self):
        self.look_to_has_been_called(time.time())

    # This has to be made public, because the server's main function might have to call it
    def look_to_has_been_called(self, call_time):
        """ Callback called when a user calls 'Look To'. """
        self._rhythm.return_to_mainloop()

        treble = Bell.from_number(1)

        # Count number of user controlled bells
        number_of_user_controlled_bells = 0
        for i in range(self.stage):
            if self._user_assigned_bell(Bell.from_index(i)):
                number_of_user_controlled_bells += 1

        self._rhythm.initialise_line(self.stage, self._user_assigned_bell(treble),
                                     call_time + 3, number_of_user_controlled_bells)

        # Move to the next row generator if it's defined
        self.row_generator = self.next_row_generator or self.row_generator
        self.next_row_generator = None

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
        """ Callback called when the Tower receives a signal that a bell has been rung. """
        if self._user_assigned_bell(bell):
            # This will give us the stroke _after_ the bell rings, we have to invert it, because
            # otherwise this will always expect the bells on the wrong stroke and no ringing will
            # ever happen
            self._rhythm.on_bell_ring(bell, not stroke, time.time())

    def _on_stop_touch(self):
        self.logger.info("Got to callback for stop touch")
        self._tower.set_is_ringing(False)
        self._is_ringing = False
        self._rhythm.return_to_mainloop()

    # Mainloop and helper methods
    def expect_bell(self, index, bell):
        """ Called to let the rhythm expect a user-controlled bell at a certain time and stroke. """
        if self._user_assigned_bell(bell):
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
        user_controlled = self._user_assigned_bell(bell)

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
            # Sit in an infinite loop whilst we're not ringing, and exit Wheatley if enough time
            # has passed
            self._last_activity_time = time.time()
            while not self._is_ringing:
                time.sleep(0.01)
                if self._server_mode and time.time() > self._last_activity_time + INACTIVITY_EXIT_TIME:
                    self.logger.info(f"Timed out - no activity for {INACTIVITY_EXIT_TIME}s. Exiting.")
                    return

            self.logger.info("Starting to ring!")
            if self._server_mode:
                self._tower.set_is_ringing(True)

            while self._is_ringing:
                self.tick()
                time.sleep(0.01)

            self.logger.info("Stopping ringing!")
            if self._server_mode:
                self._tower.set_is_ringing(False)

    def _user_assigned_bell(self, bell: Bell):
        """ True when the bell is assigned to a different user name than given to the bot """
        return not self._bot_assigned_bell(bell)

    def _bot_assigned_bell(self, bell: Bell):
        """ True when the bell is assigned to the user name given to the bot
        or bell is unassigned when user name is not set"""
        return self._tower.is_bell_assigned_to(bell, self._user_name)
