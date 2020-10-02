"""
Module that provides a convenient interface between Ringing Room and the rest of the program.
"""

import collections
import logging
from time import sleep
from typing import Optional, Callable, Dict, List, Any

import socketio

from wheatley.bell import Bell


HANDSTROKE = True
BACKSTROKE = False


def stroke_to_string(stroke: bool) -> str:
    """ Convert stroke to string for logging """
    return "HANDSTROKE" if stroke else "BACKSTROKE"


class RingingRoomTower:
    """ A class representing a tower, which will handle a single ringing-room session. """

    logger_name = "TOWER"

    def __init__(self, tower_id: int, url: str):
        """ Initialise a tower with a given room id and url. """
        self.tower_id = tower_id

        self._bell_state = []
        self._assigned_users = {}
        # A map from user IDs to the corresponding user name
        self._user_name_map: Dict[int, str] = {}

        self.invoke_on_call: Dict[str, List[Callable[[], Any]]] = collections.defaultdict(list)
        self.invoke_on_reset: List[Callable[[], Any]] = []
        self.invoke_on_bell_rung: List[Callable[[int, bool], Any]] = []
        self.invoke_on_setting_change: List[Callable[[str, Any], Any]] = []
        self.invoke_on_row_gen_change: List[Callable[[Any], Any]] = []
        self.invoke_on_stop_touch: List[Callable[[], Any]] = []

        self._url = url
        self._socket_io_client: Optional[socketio.Client] = None

        self.logger = logging.getLogger(self.logger_name)

    def __enter__(self):
        """ Called when entering a 'with' block.  Opens the socket-io connection. """
        self.logger.debug("ENTER")

        if self._socket_io_client is not None:
            raise Exception("Trying to connect twice")

        self._create_client()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when finishing a 'with' block.  Clears up the object and disconnects the session.
        """
        self.logger.debug("EXIT")
        if self._socket_io_client:
            self.logger.info("Disconnect")
            self._socket_io_client.disconnect()
            self._socket_io_client = None

    @property
    def number_of_bells(self):
        """ Returns the number of bells currently in the tower. """
        return len(self._bell_state)

    def ring_bell(self, bell: Bell, is_handstroke: bool):
        """ Send a request to the the server if the bell can be rung on the given stroke. """
        try:
            stroke = self.get_stroke(bell)
            if stroke != is_handstroke:
                self.logger.error(f"Bell {bell} on opposite stroke")
                return False

            self._emit(
                "c_bell_rung",
                {"bell": bell.number, "stroke": stroke, "tower_id": self.tower_id},
                ""
            )

            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def is_bell_assigned_to(self, bell: Bell, user_name: Optional[str]):
        """ Returns true if a given bell is assigned to the given user name. """
        try:
            assigned_user_id = self._assigned_users.get(bell, None)
            if assigned_user_id is None and user_name is None:
                return True
            return self.user_name_from_id(assigned_user_id) == user_name
        except KeyError:
            return False

    def user_name_from_id(self, user_id: int) -> str:
        """
        Converts a numerical user ID into the corresponding user name, returning None if user_id is not in
        the tower.
        """
        return self._user_name_map.get(user_id)

    def get_stroke(self, bell: Bell):
        """ Returns the stroke of a given bell. """
        if bell.index >= len(self._bell_state) or bell.index < 0:
            self.logger.error(f"Bell {bell} not in tower")
            return None

        return self._bell_state[bell.index]

    def make_call(self, call: str):
        """ Broadcasts a given call to the other users of the tower. """
        self._emit("c_call", {"call": call, "tower_id": self.tower_id}, f"Call '{call}'")

    def set_at_hand(self):
        """ Sets all the bells at hand. """
        self._emit("c_set_bells", {"tower_id": self.tower_id}, "Set at hand")

    def set_number_of_bells(self, number: int):
        """ Set the number of bells in the tower. """
        self._emit(
            "c_size_change",
            {"new_size": number, "tower_id": self.tower_id},
            f"Set number of bells '{number}'"
        )

    def set_is_ringing(self, value: bool):
        """ Broadcast to all the users that Wheatley has started or stopped ringing. """
        self._emit(
            "c_wheatley_is_ringing",
            {"is_ringing": value, "tower_id": self.tower_id},
            f"Setting is ringing to {value}"
        )

    def wait_loaded(self):
        """ Pause the thread until the socket-io connection is open and stable. """
        if self._socket_io_client is None:
            raise Exception("Not Connected")

        iteration = 0
        while not self._bell_state:
            iteration += 1
            if iteration % 50 == 0:
                self._join_tower()
                self._request_global_state()

            sleep(0.1)

    def _create_client(self):
        """ Generates the socket-io client and attaches callbacks. """
        self._socket_io_client = socketio.Client()
        self._socket_io_client.connect(self._url)
        self.logger.info(f"Connected to {self._url}")

        self._socket_io_client.on("s_bell_rung", self._on_bell_rung)
        self._socket_io_client.on("s_global_state", self._on_global_bell_state)
        self._socket_io_client.on("s_user_entered", self._on_user_entered)
        self._socket_io_client.on("s_set_userlist", self._on_user_list)
        self._socket_io_client.on("s_size_change", self._on_size_change)
        self._socket_io_client.on("s_assign_user", self._on_assign_user)
        self._socket_io_client.on("s_call", self._on_call)
        self._socket_io_client.on("s_user_left", self._on_user_leave)
        self._socket_io_client.on("s_wheatley_setting", self._on_setting_change)
        self._socket_io_client.on("s_wheatley_row_gen", self._on_row_gen_change)
        self._socket_io_client.on("s_wheatley_stop_touch", self._on_stop_touch)

        self._join_tower()
        self._request_global_state()

    def _on_setting_change(self, data):
        self.logger.info(f"RECEIVED: Settings changed: {data}\
{' (ignoring)' if len(self.invoke_on_setting_change) == 0 else ''}")

        for key, value in data.items():
            for callback in self.invoke_on_setting_change:
                callback(key, value)

    def _on_row_gen_change(self, data):
        self.logger.info(f"RECEIVED: Row gen changed: {data}\
{' (ignoring)' if len(self.invoke_on_row_gen_change) == 0 else ''}")

        for callback in self.invoke_on_row_gen_change:
            callback(data)

    def _on_stop_touch(self, data):
        self.logger.info(f"RECEIVED: Stop touch: {data}.")

        for callback in self.invoke_on_stop_touch:
            callback()

    def _on_user_leave(self, data):
        user_id_that_left = data["user_id"]
        user_name_that_left = data["username"]

        # Remove the user ID that left from our user list
        if user_id_that_left not in self._user_name_map:
            self.logger.warning(
                f"User #{user_id_that_left}:'{user_name_that_left}' left, but wasn't in the user list."
            )
        elif self._user_name_map[user_id_that_left] != data['username']:
            self.logger.warning(f"User #{user_id_that_left}:'{user_name_that_left}' left, but that ID was \
logged in as '{self._user_name_map[user_id_that_left]}'.")
            del self._user_name_map[user_id_that_left]

        bells_unassigned = []

        # Unassign all instances of that user
        for bell, user in self._assigned_users.items():
            if user == user_id_that_left:
                self._assigned_users[bell] = None

                bells_unassigned.append(bell)

        self.logger.info(
            f"RECEIVED: User #{user_id_that_left}:'{user_name_that_left}' left from bells {bells_unassigned}."
        )

    def _on_user_entered(self, data):
        """ Called when the server receives a uew user so we can update our user list. """
        # Add the new user to the user list, so we can match up their ID with their username
        self._user_name_map[data['user_id']] = data['username']

    def _on_user_list(self, user_list):
        """ Called when the server broadcasts a user list when Wheatley joins a tower. """
        for user in user_list['user_list']:
            self._user_name_map[user['user_id']] = user['username']

    def _join_tower(self):
        """ Joins the tower as an anonymous user. """
        self._emit(
            "c_join",
            {"anonymous_user": True, "tower_id": self.tower_id},
            f"Joining tower {self.tower_id}"
        )

    def _request_global_state(self):
        """ Send a request to the server to get the current state of the tower. """
        self._emit('c_request_global_state', {"tower_id": self.tower_id}, "Request state")

    def _emit(self, event: str, data, message: str):
        """ Emit a socket-io signal. """
        if self._socket_io_client is None:
            raise Exception("Not Connected")

        self._socket_io_client.emit(event, data)

        if message:
            self.logger.info(f"EMIT: {message}")

    def _on_bell_rung(self, data):
        """ Callback called when the client receives a signal that a bell has been rung. """
        self._update_bell_state(data["global_bell_state"])

        who_rang = Bell.from_number(data["who_rang"])
        for bell_ring_callback in self.invoke_on_bell_rung:
            bell_ring_callback(who_rang, self.get_stroke(who_rang))

    def _update_bell_state(self, bell_state):
        self._bell_state = bell_state

        self.logger.debug(f"RECEIVED: Bells '{['H' if x else 'B' for x in bell_state]}'")

    def _on_global_bell_state(self, data):
        """
        Callback called when receiving an update to the global tower state.
        Cannot have further callbacks assigned to it.
        """
        self._update_bell_state(data["global_bell_state"])
        for invoke_callback in self.invoke_on_reset:
            invoke_callback()

    def _on_size_change(self, data):
        """ Callback called when the number of bells in the room changes. """
        new_size = data["size"]
        if new_size != self.number_of_bells:
            # Remove the user who's bells have been removed (so that returning to a stage doesn't make
            # Wheatley think the bells are still assigned)
            self._assigned_users = {bell: user for (bell, user) in self._assigned_users.items()
                                               if bell.number <= new_size}
            # Set the bells at handstroke
            self._bell_state = self._bells_set_at_hand(new_size)
            # Handle all the callbacks
            self.logger.info(f"RECEIVED: New tower size '{new_size}'")
            for invoke_callback in self.invoke_on_reset:
                invoke_callback()

    def _on_assign_user(self, data):
        """ Callback called when a bell assignment is changed. """
        bell = Bell.from_number(data["bell"])
        user = data["user"] or None

        self._assigned_users[bell] = user

        assert isinstance(user, int) or user is None, \
               f"User ID {user} is not an integer (it has type {type(user)})."

        if user:
            self.logger.info(f"RECEIVED: Assigned bell '{bell}' to '{self.user_name_from_id(user)}'")
        else:
            self.logger.info(f"RECEIVED: Unassigned bell '{bell}'")

    def _on_call(self, data):
        """ Callback called when a call is made. """
        call = data["call"]
        self.logger.info(f"RECEIVED: Call '{call}'")

        found_callback = False
        for call_callback in self.invoke_on_call.get(call, []):
            call_callback()
            found_callback = True
        if not found_callback:
            self.logger.warning(f"No callback found for '{call}'")

    @staticmethod
    def _bells_set_at_hand(number: int):
        """ Returns the representation of `number` bells, all set at handstroke. """
        return [HANDSTROKE for _ in range(number)]
