"""
Module to contain the Bot class, which acts as 'glue' to combine the rhythm, row generation and
socket-io communication provided by the Rhythm, RowGenerator and Tower objects into a useful
program.
"""

import time
import logging
from typing import Optional, Any

from wheatley import calls
from wheatley.aliases import JSON, Row
from wheatley.stroke import Stroke
from wheatley.bell import Bell, MAX_BELL
from wheatley.rhythm import Rhythm
from wheatley.row_generation.helpers import rounds
from wheatley.tower import RingingRoomTower
from wheatley.parsing import to_bool, json_to_row_generator, RowGenParseError
from wheatley.row_generation import RowGenerator


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
                 stop_at_rounds: bool, rhythm: Rhythm, user_name: Optional[str] = None,
                 server_instance_id: Optional[int] = None) -> None:
        """ Initialise a Bot with all the parts it needs to run. """
        # If this is None then Wheatley is in client mode, otherwise Wheatley is in server mode
        self._server_instance_id = server_instance_id
        self._last_activity_time = time.time()

        self._rhythm = rhythm
        self._do_up_down_in = do_up_down_in
        self._stop_at_rounds = stop_at_rounds
        self._user_name = user_name

        self.row_generator = row_generator
        # This is the row generator that will be used after 'Look to' is called for the next time, allowing
        # for changing the method or composition whilst Wheatley is running.
        self.next_row_generator: Optional[RowGenerator] = None

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
        self._rounds: Row = rounds(MAX_BELL)
        self._row: Row = self._rounds

        self.logger = logging.getLogger(self.logger_name)

        # Log what we're going to ring
        self.logger.info(f"Wheatley will ring {self.row_generator.summary_string()}")

    # Convenient properties that are frequently used
    @property
    def stroke(self) -> Stroke:
        """ Returns true if the current row (determined by self._row_number) represents a handstroke. """
        return Stroke.from_index(self._row_number)

    @property
    def number_of_bells(self) -> int:
        """ Convenient property to find the number of bells in the current tower. """
        return self._tower.number_of_bells

    @property
    def _server_mode(self) -> bool:
        return self._server_instance_id is not None

    # Callbacks
    def _on_setting_change(self, key: str, value: Any) -> None:
        def log_invalid_key(message: str) -> None:
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

    def _on_row_gen_change(self, row_gen_json: JSON) -> None:
        try:
            self.next_row_generator = json_to_row_generator(row_gen_json, self.logger)
            self.logger.info(f"Next touch, Wheatley will ring {self.next_row_generator.summary_string()}")
        except RowGenParseError as e:
            self.logger.warning(e)

    def _on_size_change(self) -> None:
        self._check_number_of_bells()
        self._rounds = rounds(self.number_of_bells)

    def _check_number_of_bells(self) -> bool:
        """ Returns whether Wheatley can ring with the current number of bells with reasons why not """
        if self.row_generator.stage == 0:
            self.logger.debug("Place holder row generator. Wheatley will not ring!")
            return False
        if self._tower.number_of_bells < self.row_generator.stage:
            self.logger.warning(f"Row generation requires at least {self.row_generator.stage} bells, "
                                + f"but the current tower has {self._tower.number_of_bells}. "
                                + "Wheatley will not ring!")
            return False
        if self._tower.number_of_bells > self.row_generator.stage + 1:
            if self.row_generator.stage % 2:
                expected = self.row_generator.stage + 1
            else:
                expected = self.row_generator.stage
            self.logger.info(f"Current tower has more bells ({self._tower.number_of_bells}) than expected "
                             + f"({expected}). Wheatley will add extra cover bells.")
        return True

    def _on_look_to(self) -> None:
        if self._check_number_of_bells():
            self.look_to_has_been_called(time.time())
        # All Wheatley instances should return a 'Roll Call' message after `Look To` is called.
        if self._server_instance_id is not None:
            self._tower.emit_roll_call(self._server_instance_id)

    # This has to be made public, because the server's main function might have to call it
    def look_to_has_been_called(self, call_time: float) -> None:
        """ Callback called when a user calls 'Look To'. """
        self._rhythm.return_to_mainloop()

        treble = self._rounds[0]

        # Count number of user controlled bells
        number_of_user_controlled_bells = sum(1 for bell in self._rounds if self._user_assigned_bell(bell))

        self._rhythm.initialise_line(self.number_of_bells, self._user_assigned_bell(treble),
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

    def _on_go(self) -> None:
        """ Callback called when a user calls 'Go'. """
        if self._is_ringing_rounds:
            self._should_start_method = True

    def _on_bob(self) -> None:
        """ Callback called when a user calls 'Bob'. """
        self.row_generator.set_bob()

    def _on_single(self) -> None:
        """ Callback called when a user calls 'Single'. """
        self.row_generator.set_single()

    def _on_thats_all(self) -> None:
        """ Callback called when a user calls 'That`s All'. """
        self._should_start_ringing_rounds = True

    def _on_stand_next(self) -> None:
        """ Callback called when a user calls 'Stand Next'. """
        self._should_stand = True

    def _on_bell_ring(self, bell: Bell, stroke: Stroke) -> None:
        """ Callback called when the Tower receives a signal that a bell has been rung. """
        if self._user_assigned_bell(bell):
            # This will give us the stroke _after_ the bell rings, we have to invert it, because
            # otherwise this will always expect the bells on the wrong stroke and no ringing will
            # ever happen
            self._rhythm.on_bell_ring(bell, stroke.opposite(), time.time())

    def _on_stop_touch(self) -> None:
        self.logger.info("Got to callback for stop touch")
        self._tower.set_is_ringing(False)
        self._is_ringing = False
        self._rhythm.return_to_mainloop()

    # Mainloop and helper methods
    def expect_bell(self, index: int, bell: Bell) -> None:
        """ Called to let the rhythm expect a user-controlled bell at a certain time and stroke. """
        if self._user_assigned_bell(bell):
            self._rhythm.expect_bell(
                bell,
                self._row_number,
                index,
                self.stroke
            )

    def start_next_row(self) -> None:
        """
        Creates a new row from the row generator and tells the rhythm to expect the new bells.
        """

        if self._is_ringing_rounds:
            self._row = self._rounds
        else:
            self._row = self.row_generator.next_row(self.stroke)
            if len(self._row) < len(self._rounds):
                # Add cover bells if needed
                self._row.extend(self._rounds[len(self._row):])

        for (index, bell) in enumerate(self._row):
            self.expect_bell(index, bell)

    def start_method(self) -> None:
        """
        Called when the ringing is about to go into changes.
        Resets the row_generator and starts the next row.
        """
        if self._check_number_of_bells():
            self.row_generator.reset()
            self.start_next_row()

    def tick(self) -> None:
        """ Move the ringing on by one place """

        bell = self._row[self._place]
        user_controlled = self._user_assigned_bell(bell)

        self._rhythm.wait_for_bell_time(time.time(), bell, self._row_number, self._place,
                                        user_controlled, self.stroke)

        if not user_controlled:
            self._tower.ring_bell(bell, self.stroke)

        self._place += 1

        if self._place >= self.number_of_bells:
            # Determine if we're finishing a handstroke
            has_just_rung_rounds = self._row == self._rounds

            # Generate the next row and update row indices
            self._row_number += 1
            self._place = 0
            self.start_next_row()

            next_stroke = Stroke.from_index(self._row_number)

            # ===== SET FLAGS FOR HANDBELL-STYLE RINGING =====

            # Implement handbell-style 'up down in'
            if self._do_up_down_in and self._is_ringing_rounds and self._row_number == 2:
                self._should_start_method = True

            # Implement handbell-style stopping at rounds
            if self._stop_at_rounds and has_just_rung_rounds and not self._is_ringing_rounds:
                self._should_stand = False
                self._is_ringing = False

            # ===== CONVERT THE FLAGS INTO ACTIONS =====

            if self._should_start_method and self._is_ringing_rounds \
               and next_stroke == self.row_generator.start_stroke():
                self._should_start_method = False
                self._is_ringing_rounds = False
                self.start_method()

            # If we're starting a handstroke, we should convert all the flags into actions
            if next_stroke.is_hand():
                if self._should_stand:
                    self._should_stand = False
                    self._is_ringing = False

                if self._should_start_ringing_rounds and not self._is_ringing_rounds:
                    self._should_start_ringing_rounds = False
                    self._is_ringing_rounds = True

    def main_loop(self) -> None:
        """
        The main_loop of the bot.
        The main thread will get stuck forever in this function whilst the bot rings.
        """
        while True:
            # Log a message to say that Wheatley is waiting for 'Look To!'
            self.logger.info("Waiting for 'Look To!'...")
            # Sit in an infinite loop whilst we're not ringing, and exit Wheatley if enough time
            # has passed
            self._last_activity_time = time.time()
            while not self._is_ringing:
                time.sleep(0.01)
                if self._server_mode and time.time() > self._last_activity_time + INACTIVITY_EXIT_TIME:
                    self.logger.info(f"Timed out - no activity for {INACTIVITY_EXIT_TIME}s. Exiting.")
                    return

            self.logger.info(f"Starting to ring {self.row_generator.summary_string()}")
            if self._server_mode:
                self._tower.set_is_ringing(True)

            while self._is_ringing:
                self.tick()
                time.sleep(0.01)

            self.logger.info("Stopping ringing!")
            if self._server_mode:
                self._tower.set_is_ringing(False)

    def _user_assigned_bell(self, bell: Bell) -> bool:
        """ True when the bell is assigned to a different user name than given to the bot """
        return not self._bot_assigned_bell(bell)

    def _bot_assigned_bell(self, bell: Bell) -> bool:
        """ True when the bell is assigned to the user name given to the bot
        or bell is unassigned when user name is not set"""
        return self._tower.is_bell_assigned_to(bell, self._user_name)
