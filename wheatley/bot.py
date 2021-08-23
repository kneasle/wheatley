"""
Module to contain the Bot class, which acts as 'glue' to combine the rhythm, row generation and
SocketIO communication provided by the Rhythm, RowGenerator and Tower objects into a useful program.
"""

import time
import logging
import threading
from typing import Optional, Any, List

from wheatley import calls
from wheatley.aliases import JSON, Row
from wheatley.stroke import Stroke
from wheatley.bell import Bell
from wheatley.rhythm import Rhythm
from wheatley.row_generation.helpers import generate_starting_row, rounds
from wheatley.tower import RingingRoomTower
from wheatley.parsing import to_bool, json_to_row_generator, RowGenParseError
from wheatley.row_generation import RowGenerator


# Number of seconds that Wheatley is not ringing before Wheatley will return from the mainloop
# Only applies when Wheatley is running in server mode
INACTIVITY_EXIT_TIME = 300


# How long it takes Bryn to say 'Look To'.  This is the length of time that Wheatley will wait
# between receiving the 'Look To' signal and when the first stroke is expected
LOOK_TO_DURATION = 3.0  # seconds


# Bot holds a lot of state, allow it to have more fields
# pylint: disable=too-many-instance-attributes
class Bot:
    """
    A class to hold all the information that Wheatley will use to glue together the rhythm,
    row_gen and socket-io parts together into a useful program.
    """

    logger_name = "BOT"

    def __init__(
        self,
        tower: RingingRoomTower,
        row_generator: RowGenerator,
        do_up_down_in: bool,
        stop_at_rounds: bool,
        call_comps: bool,
        rhythm: Rhythm,
        user_name: Optional[str] = None,
        server_instance_id: Optional[int] = None,
    ) -> None:
        """Initialise a Bot with all the parts it needs to run."""
        # If this is None then Wheatley is in client mode, otherwise Wheatley is in server mode
        self._server_instance_id = server_instance_id
        self._last_activity_time = time.time()

        self._rhythm = rhythm
        self._do_up_down_in = do_up_down_in
        self._stop_at_rounds = stop_at_rounds
        self._call_comps = call_comps
        self._user_name = user_name

        self.row_generator = row_generator
        # This is the row generator that will be used after 'Look to' is called for the next time,
        # allowing for changing the method or composition whilst Wheatley is running.  A mutex lock
        # is required to prevent the following race condition:
        # - The tower size is reduced, and a `s_size_change` signal is sent.  This causes
        #   `self._check_number_of_bells` to be called on `self.next_row_generator`.  This checks
        #   whether or not the stage is too large to fit in the current tower.  Suppose that this
        #   check passes.
        # - Between the check and the body of the `if` statement, a new row generator arrives in the
        #   `s_wheatley_row_gen` signal.  This has the new stage, and gets assigned to
        #   `self.next_row_generator`
        # - The `s_size_change` thread continues executing, and sets `self.next_row_generator` to
        #   `None`, thus overwriting the **new** row generator (which was perfectly fine).
        self.next_row_generator_lock = threading.Lock()
        self.next_row_generator: Optional[RowGenerator] = None

        self._tower = tower

        self._tower.invoke_on_call[calls.LOOK_TO].append(self._on_look_to)
        self._tower.invoke_on_call[calls.GO].append(self._on_go)
        self._tower.invoke_on_call[calls.BOB].append(self._on_bob)
        self._tower.invoke_on_call[calls.SINGLE].append(self._on_single)
        self._tower.invoke_on_call[calls.THATS_ALL].append(self._on_thats_all)
        self._tower.invoke_on_call[calls.ROUNDS].append(self._on_rounds)
        self._tower.invoke_on_call[calls.STAND].append(self._on_stand_next)
        self._tower.invoke_on_bell_rung.append(self._on_bell_ring)
        self._tower.invoke_on_reset.append(self._on_size_change)
        if self._server_mode:
            self._tower.invoke_on_setting_change.append(self._on_setting_change)
            self._tower.invoke_on_row_gen_change.append(self._on_row_gen_change)
            self._tower.invoke_on_stop_touch.append(self._on_stop_touch)

        self._is_ringing = False
        self._is_ringing_rounds = False
        self._is_ringing_opening_row = True
        # This is used as a counter - once `Go` or `Look To` is received, the number of rounds left
        # is calculated and then decremented at the start of every subsequent row until it reaches
        # 0, at which point the method starts.  We keep a counter rather than a simple flag so that
        # calls can be called **before** going into changes when Wheatley is calling (useful for
        # calling the first method name in spliced and early calls in Original, Erin, etc.).  The
        # value `None` is used to represent the case where we don't know when we will be starting
        # the method (and therefore there it makes no sense to decrement this counter).
        self._rounds_left_before_method: Optional[int] = None
        self._rows_left_before_rounds: Optional[int] = None
        self._should_stand = False

        self._row_number = 0
        self._place = 0
        self._opening_row: Row = row_generator.start_row
        self._rounds: Row = rounds(self.number_of_bells)
        self._row: Row = self._rounds

        # This is used because the row's calls are generated at the **end** of each row (or on
        # `Look To`), but need to be called at the **start** of the next row.
        self._calls: List[str] = []

        self.logger = logging.getLogger(self.logger_name)

        # Log what we're going to ring, and how to stop Wheatley
        self.logger.info(f"Wheatley will ring {self.row_generator.summary_string()}")
        self.logger.info("Press `Control-C` to stop Wheatley ringing, e.g. to change method.")

    # Convenient properties that are frequently used
    @property
    def stroke(self) -> Stroke:
        """Returns true if the current row (determined by self._row_number) represents a handstroke."""
        return Stroke.from_index(self._row_number)

    @property
    def number_of_bells(self) -> int:
        """Convenient property to find the number of bells in the current tower."""
        return self._tower.number_of_bells

    @property
    def _server_mode(self) -> bool:
        return self._server_instance_id is not None

    # Callbacks
    def _on_setting_change(self, key: str, value: Any) -> None:
        def log_invalid_key(message: str) -> None:
            self.logger.warning(f"Invalid value for {key}: {message}")

        if key == "use_up_down_in":
            try:
                self._do_up_down_in = to_bool(value)
                self.logger.info(f"Setting 'use_up_down_in' to {self._do_up_down_in}")
            except ValueError:
                log_invalid_key(f"{value} cannot be converted into a bool")
        elif key == "stop_at_rounds":
            try:
                self._stop_at_rounds = to_bool(value)
                self.logger.info(f"Setting 'stop_at_rounds' to {value}")
            except ValueError:
                log_invalid_key(f"{value} cannot be converted into a bool")
        else:
            self._rhythm.change_setting(key, value, time.time())

    def _on_row_gen_change(self, row_gen_json: JSON) -> None:
        try:
            # We need a mutex lock on `self.next_row_generator` to prevent a possible race
            # conditions when reducing the tower size (see the definition of
            # `self.next_row_generator` in `__init__` for more details)
            with self.next_row_generator_lock:
                self.next_row_generator = json_to_row_generator(row_gen_json, self.logger)

            self.logger.info(f"Next touch, Wheatley will ring {self.next_row_generator.summary_string()}")
        except RowGenParseError as e:
            self.logger.warning(e)

    def _on_size_change(self) -> None:
        self._check_number_of_bells()
        self._opening_row = generate_starting_row(self.number_of_bells, self.row_generator.custom_start_row)
        self._rounds = rounds(self.number_of_bells)

        self._check_starting_row()  # Check that the current row gen is OK (otherwise warn the user)

        # Check that `self.next_row_generator` has the right stage
        with self.next_row_generator_lock:
            if self.next_row_generator is not None and not self._check_number_of_bells(
                self.next_row_generator, silent=True
            ):
                self.logger.warning("Next row gen needed too many bells, so is being removed.")
                # If the `next_row_generator` can't be rung on the new stage, then remove it.
                self.next_row_generator = None

    def _check_starting_row(self) -> bool:
        if (
            self.row_generator.custom_start_row is not None
            and len(self.row_generator.custom_start_row) < self.number_of_bells
        ):
            self.logger.info(
                f"The starting row '{self.row_generator.custom_start_row}' "
                + f"contains fewer bells than the tower ({self.number_of_bells}). "
                + "Wheatley will add the extra bells to the end of the change."
            )

        if len(self._opening_row) != self.number_of_bells:
            self.logger.warning(
                f"The current tower has fewer bells ({self.number_of_bells}) "
                + f"than the starting row {self._opening_row}. Wheatley will not ring!"
            )
            return False
        return True

    def _check_number_of_bells(self, row_gen: Optional[RowGenerator] = None, silent: bool = False) -> bool:
        """Returns whether Wheatley can ring with the current number of bells with reasons why not"""

        # If the user doesn't pass the `row_gen` argument, then default to `self.row_generator`
        row_gen = row_gen or self.row_generator

        if row_gen.stage == 0:
            self.logger.debug("Place holder row generator. Wheatley will not ring!")
            return False
        if self._tower.number_of_bells < row_gen.stage:
            if not silent:  # only log if `silent` isn't set
                self.logger.warning(
                    f"Row generation requires at least {row_gen.stage} bells, "
                    + f"but the current tower has {self.number_of_bells}. "
                    + "Wheatley will not ring!"
                )
            return False
        if self._tower.number_of_bells > row_gen.stage + 1 and row_gen.custom_start_row is None:
            if row_gen.stage % 2:
                expected = row_gen.stage + 1
            else:
                expected = row_gen.stage

            if not silent:  # only log if `silent` isn't set
                self.logger.info(
                    f"Current tower has more bells ({self.number_of_bells}) than expected "
                    + f"({expected}). Wheatley will add extra cover bells."
                )
        return True

    def _on_look_to(self) -> None:
        if self._check_starting_row() and self._check_number_of_bells():
            self.look_to_has_been_called(time.time())

    # This is public because it's used by `wheatley.main.server_main`.  `server_main` calls it
    # because, when running Wheatley on the RR servers, it is entirely possible that a new Wheatley
    # process is invoked a few seconds **after** 'Look To' has been called.  This does not
    # necessarily make Wheatley start late (because Bryn takes ~3 seconds to say 'Look To'), but the
    # new Wheatley instance needs to know _when_ 'Look To' was called (otherwise the new instance
    # doesn't know when to start ringing).  To achieve this, the RR server remembers the timestamp
    # of `Look To` and passes it to the new instance through the `--look-to-time` argument (defined
    # in `server_main`).  The main function then creates the `Bot` singleton and immediately calls
    # `look_to_has_been_called`, forwarding the `--look-to-time` as the argument.
    #
    # **side note**: system clocks on different computers are really rarely in sync, so it's
    # generally a very bad idea to pass timestamps between two processes, in case they end up
    # running on different machines.  However, in our case, the only time `--look-to-time` is used
    # is when Wheatley is running on the same machine as the RR server itself.  So (in this case) we
    # are fine.
    def look_to_has_been_called(self, call_time: float) -> None:
        """Callback called when a user calls 'Look To'."""
        self._rhythm.return_to_mainloop()

        treble = self._rounds[0]

        # Count number of user controlled bells
        number_of_user_controlled_bells = sum(1 for bell in self._rounds if self._user_assigned_bell(bell))

        self._rhythm.initialise_line(
            self.number_of_bells,
            self._user_assigned_bell(treble),
            call_time + LOOK_TO_DURATION,
            number_of_user_controlled_bells,
        )

        # Move to the next row generator if it's defined
        self.row_generator = self.next_row_generator or self.row_generator
        self.next_row_generator = None

        # Clear all the flags and counters
        self._should_stand = False
        self._rows_left_before_rounds = None
        # Set _rounds_left_before_method if we are ringing up-down-in (3 rounds for backstroke
        # start; 2 for handstroke)
        if not self._do_up_down_in:
            self._rounds_left_before_method = None
        elif self.row_generator.start_stroke().is_hand():
            self._rounds_left_before_method = 2
        else:
            self._rounds_left_before_method = 3

        # Reset the state, so that Wheatley starts by ringing rounds
        self._is_ringing = True
        self._is_ringing_rounds = True
        self._is_ringing_opening_row = True

        # Start at the first place of the first row
        self.start_next_row(is_first_row=True)

    def _on_go(self) -> None:
        """Callback called when a user calls 'Go'."""
        if self._is_ringing_rounds or self._is_ringing_opening_row:
            # Calculate how many more rows of rounds we should ring before going into changes (1 if
            # the person called 'Go' on the same stroke as the RowGenerator starts, otherwise 0).
            # These values are one less than expected because we are setting
            # _rounds_left_before_method **after** the row has started.
            self._rounds_left_before_method = 1 if self.stroke == self.row_generator.start_stroke() else 0
            # Make sure to call all of the calls that we have missed in the right order (in case the
            # person calling `Go` called it stupidly late)
            early_calls = [
                (ind, calls)
                for (ind, calls) in self.row_generator.early_calls().items()
                if ind > self._rounds_left_before_method
            ]
            # Sort early calls by the number of rows **before** the method start.  Note that we are
            # sorting by a quantity that counts **down** with time, hence the reversed sort.
            early_calls.sort(key=lambda x: x[0], reverse=True)
            # In this case, we don't want to wait until the next row before making these calls
            # because the rows on which these calls should have been called have already passed.
            # Therefore, we simply get them out as quickly as possible so they have the best chance
            # of being heard.
            for (_, c) in early_calls:
                self._make_calls(c)

    def _on_bob(self) -> None:
        """Callback called when a user calls 'Bob'."""
        self.row_generator.set_bob()

    def _on_single(self) -> None:
        """Callback called when a user calls 'Single'."""
        self.row_generator.set_single()

    def _on_thats_all(self) -> None:
        """Callback called when a user calls 'That`s All'."""
        # We set this to one, because we expect one clear row between the call and rounds
        self._rows_left_before_rounds = 1

    def _on_rounds(self) -> None:
        """Callback called when a user calls 'Rounds'."""
        # We set this to one, because we expect one clear row between the call and rounds
        self._is_ringing_opening_row = True

    def _on_stand_next(self) -> None:
        """Callback called when a user calls 'Stand Next'."""
        self._should_stand = True

    def _on_bell_ring(self, bell: Bell, stroke: Stroke) -> None:
        """Callback called when the Tower receives a signal that a bell has been rung."""
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
        """Called to let the rhythm expect a user-controlled bell at a certain time and stroke."""
        if self._user_assigned_bell(bell):
            self._rhythm.expect_bell(bell, self._row_number, index, self.stroke)

    def generate_next_row(self) -> None:
        """Creates a new row from the row generator and tells the rhythm to expect the new bells."""
        if self._is_ringing_opening_row:
            self._row = self._opening_row
        elif self._is_ringing_rounds:
            self._row = self._rounds
        else:
            self._row, self._calls = self.row_generator.next_row_and_calls(self.stroke)
            # Add cover bells if needed
            if len(self._row) < len(self._opening_row):
                self._row = Row(self._row + self._opening_row[len(self._row) :])

        bells = " ".join([str(bell) for bell in self._row])
        self.logger.info(f"ROW: {bells}")

    def start_next_row(self, is_first_row: bool) -> None:
        """Updates state of bot ready to ring the next row / stop ringing"""
        # Generate the next row and update row indices
        self._place = 0
        if is_first_row:
            self._row_number = 0
        else:
            self._row_number += 1

        # Useful local variables
        has_just_rung_rounds = self._row == self._rounds
        next_stroke = Stroke.from_index(self._row_number)

        # Implement handbell-style stopping at rounds
        if self._stop_at_rounds and has_just_rung_rounds and not self._is_ringing_opening_row:
            self._should_stand = True

        # Set any early calls specified by the row generator to be called at the start of the next
        # row
        if self._rounds_left_before_method is not None:
            self._calls = self.row_generator.early_calls().get(self._rounds_left_before_method) or []

        # Start the method if necessary
        if self._rounds_left_before_method == 0:
            # Sanity check that we are in fact starting on the correct stroke (which is no longer
            # trivially guaranteed since we use a counter rather than a flag to determine when to
            # start the method)
            assert next_stroke == self.row_generator.start_stroke()
            self._rounds_left_before_method = None
            self._is_ringing_rounds = False
            self._is_ringing_opening_row = False
            # If the tower size somehow changed, then call 'Stand' but keep ringing rounds (Wheatley
            # calling 'Stand' will still generate a callback to `self._on_stand_next`, so we don't
            # need to handle that here)
            if not self._check_number_of_bells():
                self._make_call("Stand")
                self._is_ringing_rounds = True
            self.row_generator.reset()
        if self._rounds_left_before_method is not None:
            self._rounds_left_before_method -= 1

        # If we're starting a handstroke ...
        if next_stroke.is_hand():
            # ... and 'Stand' has been called, then stand
            if self._should_stand:
                self._should_stand = False
                self._is_ringing = False

        # There are two cases for coming round:
        # 1. Someone calls 'That's All' and rounds appears
        #       (or)
        # 2. Someone calls 'That's All', one clear row has elapsed
        if self._rows_left_before_rounds == 0 or (
            has_just_rung_rounds and self._rows_left_before_rounds is not None
        ):
            self._rows_left_before_rounds = None
            self._is_ringing_rounds = True
        if self._rows_left_before_rounds is not None:
            self._rows_left_before_rounds -= 1

        # If we've set `_is_ringing` to False, then no more rounds can happen so early return to
        # avoid erroneous calls
        if not self._is_ringing:
            return

        # Generate the next row, and tell the rhythm detection where the next row's bells are
        # expected to ring
        self.generate_next_row()
        for (index, bell) in enumerate(self._row):
            self.expect_bell(index, bell)

    def tick(self) -> None:
        """
        Move the ringing on by one place.  This 'tick' function is called once every time a bell is
        rung.
        """
        bell = self._row[self._place]
        user_controlled = self._user_assigned_bell(bell)

        self._rhythm.wait_for_bell_time(
            time.time(), bell, self._row_number, self._place, user_controlled, self.stroke
        )

        if not user_controlled:
            self._tower.ring_bell(bell, self.stroke)

        # If we are ringing the first bell in the row, then also make any calls that are needed.
        if self._place == 0:
            self._make_calls(self._calls)

        # Move one place through the ringing
        self._place += 1

        # Start a new row if we get to a place that's bigger than the number of bells
        if self._place >= self.number_of_bells:
            self.start_next_row(is_first_row=False)

    def main_loop(self) -> None:
        """
        Wheatley's main loop.  The main thread will get stuck forever in this function whilst
        Wheatley rings.  The outer main-loop contains two sub-loops: the first one for Wheatley
        waiting to ring (triggered by `Look To`), where the second one makes Wheatley ring
        by repeatedly calling `self.tick()`.
        """
        while True:
            # Log a message to say that Wheatley is waiting for 'Look To!'
            self.logger.info("Waiting for 'Look To'...")

            # Waiting to ring: Sit in an infinite loop whilst we're not ringing, and exit Wheatley
            # if the tower is inactive for long enough.
            self._last_activity_time = time.time()
            while not self._is_ringing:
                time.sleep(0.01)
                if self._server_mode and time.time() > self._last_activity_time + INACTIVITY_EXIT_TIME:
                    self.logger.info(f"Timed out - no activity for {INACTIVITY_EXIT_TIME}s. Exiting.")
                    return

            # Start ringing: note that this code runs **IMMEDIATELY** after `Look To` is called, but
            # `self._rhythm` is told to wait until after Bryn has finished saying `Look To`.
            if self._do_up_down_in:
                self.logger.info(f"Starting to ring {self.row_generator.summary_string()}")
            else:
                self.logger.info(f"Waiting for 'Go' to ring {self.row_generator.summary_string()}...")
            if self._server_mode:
                self._tower.set_is_ringing(True)  # Set text in Wheatley box to 'Wheatley is ringing...'

                # All Wheatley instances should return a 'Roll Call' message after `Look To`, but
                # **only** if they are actually able to start ringing.  This prevents a problem
                # where Wheatleys could get stuck in a state where they respond to the roll-call but
                # are unable to ring.  The RR server gets a roll-call reply, assumes everything is
                # fine, and ends up creating a 'zombie' Wheatley instance.  To the user, this just
                # looks like Wheatley has gone off in a huff
                assert self._server_instance_id is not None
                self._tower.emit_roll_call(self._server_instance_id)

            # Repeatedly ring until the ringing stops
            while self._is_ringing:
                self.tick()
                # Add a tiny bit of extra delay between each stroke so that Wheatley doesn't DDoS
                # Ringing Room if `self._rhythm.wait_for_bell_time()` returns immediately
                time.sleep(0.01)

            # Finish ringing
            self.logger.info("Stopping ringing!")
            if self._server_mode:
                self._tower.set_is_ringing(False)  # Set text in Wheatley box to 'Wheatley will ring...'

    def _user_assigned_bell(self, bell: Bell) -> bool:
        """Returns `True` if this bell is not assigned to Wheatley."""
        return not self._bot_assigned_bell(bell)

    def _bot_assigned_bell(self, bell: Bell) -> bool:
        """Returns `True` if this bell **is** assigned to Wheatley."""
        return self._tower.is_bell_assigned_to(bell, self._user_name)

    def _make_calls(self, call_list: List[str]) -> None:
        """Broadcast a sequence of calls"""
        for c in call_list:
            self._make_call(c)

    def _make_call(self, call: str) -> None:
        """Broadcast a call, unless we've been told not to call anything."""
        if self._call_comps:
            self._tower.make_call(call)
