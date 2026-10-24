"""
Module that provides a convenient interface between Ringing Room and the rest of the program.
"""

import collections
import json
import logging
import threading
from typing import Optional, Callable, Dict, List, Any, Tuple

import websocket  # type: ignore

from wheatley.aliases import JSON
from wheatley.bell import Bell
from wheatley.server_url import websocket_url, TowerNotFoundError, InvalidURLError
from wheatley.stroke import Stroke

# How long to wait for the server to accept the connection, and then to send everything a joiner needs
CONNECT_TIMEOUT = 10  # seconds
LOAD_TIMEOUT = 10  # seconds

# `s_error` reasons after which the server closes the connection, because Wheatley can't carry on
FATAL_REASONS = {
    "invalid_name",
    "bots_not_permitted",
    "invalid_token",
    "server_restarting",
}


class RingingRoomTowerConnectError(Exception):
    """A class for error in logic connecting."""


# Pylint doesn't like how much state a tower holds, but it is all about the one connection
# pylint: disable=too-many-instance-attributes
class RingingRoomTower:
    """
    A class representing a tower, which will handle a single ringing-room session.  Wheatley joins as a
    'bot': a connection with no login, which Ringing Room lets ring the bells that nobody has (or, if
    people have assigned it some bells, only those) and make the calls that a touch needs.  In host mode it
    rings only the bells that are assigned to it, as everyone else does.
    """

    logger_name = "TOWER"

    def __init__(self, tower_id: int, url: str, name: Optional[str] = None) -> None:
        """
        Initialise a tower with a given room id and the address of its server.  `name` is what Ringing
        Room will call Wheatley (it picks one if this is `None`).
        """
        self.tower_id = tower_id
        self._name = name
        self._ws_url = websocket_url(tower_id, url)

        self._bell_state: List[Stroke] = []
        # Who each assigned bell is assigned to (unassigned bells are not in here).  This and
        # `_my_user_id` are written by the socket's thread and read by the main one.
        self._assigned_users: Dict[Bell, int] = {}
        self._assignment_lock = threading.Lock()
        # A map from user IDs to the corresponding user name
        self._user_name_map: Dict[int, str] = {}
        # Wheatley's own id in the tower, from his own `s_user_entered`, the last thing in the join burst
        self._my_user_id: Optional[int] = None
        # Whether the tower is in host mode, where everyone rings only the bells assigned to them
        self._host_mode = False

        self.invoke_on_call: Dict[str, List[Callable[[], Any]]] = collections.defaultdict(list)
        self.invoke_on_reset: List[Callable[[], Any]] = []
        self.invoke_on_bell_rung: List[Callable[[Bell, Stroke], Any]] = []
        self.invoke_on_setting_change: List[Callable[[str, Any], Any]] = []
        self.invoke_on_row_gen_change: List[Callable[[Any], Any]] = []
        # Never invoked: Ringing Room no longer sends `s_wheatley_stop_touch`
        self.invoke_on_stop_touch: List[Callable[[], Any]] = []
        # Invoked once, when the connection has gone
        self.invoke_on_close: List[Callable[[], Any]] = []

        self._ws: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self._loaded = threading.Event()
        self._closed = threading.Event()
        # Why the connection ended, if the server said: (reason, message)
        self._fatal_error: Optional[Tuple[str, str]] = None
        # What the server last said about sending too fast: if it then closes the connection, that is why
        self._last_rate_limit_message: Optional[str] = None

        self.logger = logging.getLogger(self.logger_name)

    def __enter__(self) -> Any:
        """Called when entering a 'with' block.  Opens the WebSocket and joins the tower."""
        self.logger.debug("ENTER")

        if self._ws is not None:
            raise RingingRoomTowerConnectError("Trying to connect twice")

        self._connect()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Called when finishing a 'with' block.  Clears up the object and disconnects the session.
        """
        self.logger.debug("EXIT")
        if self._ws:
            self.logger.info("Disconnect")
            ws, self._ws = self._ws, None
            try:
                ws.close()
            except websocket.WebSocketException:
                pass
            if self._thread is not None:
                self._thread.join(timeout=2)

    @property
    def number_of_bells(self) -> int:
        """Returns the number of bells currently in the tower."""
        return len(self._bell_state)

    @property
    def is_closed(self) -> bool:
        """Whether the connection has gone, because it was closed or lost."""
        return self._closed.is_set()

    @property
    def closed_reason(self) -> Optional[str]:
        """What Ringing Room said about why it ended the connection, if it said anything."""
        if self._fatal_error:
            return self._fatal_error[1]
        if self._closed.is_set():
            return self._last_rate_limit_message
        return None

    def ring_bell(self, bell: Bell, expected_stroke: Stroke) -> bool:
        """Send a request to the the server if the bell can be rung on the given stroke."""
        try:
            stroke = self.get_stroke(bell)
            if stroke != expected_stroke:
                self.logger.error(f"Bell {bell} on opposite stroke")
                return False

            bell_num: int = bell.number
            is_handstroke: bool = stroke.is_hand()
            self._emit("c_bell_rung", {"bell": bell_num, "stroke": is_handstroke})

            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def should_ring(self, bell: Bell) -> bool:
        """
        Whether Wheatley should ring this bell.  If people have assigned him any bells then those are
        the ones he rings; otherwise he rings every bell that nobody has.  In host mode he rings only the
        bells assigned to him, which may be none (and the server would refuse any other).
        """
        with self._assignment_lock:
            mine = [b for b, user in self._assigned_users.items() if user == self._my_user_id]
            if mine or self._host_mode:
                return bell in mine
            return bell not in self._assigned_users

    def user_name_from_id(self, user_id: int) -> Optional[str]:
        """
        Converts a numerical user ID into the corresponding user name, returning None if user_id is not in
        the tower.
        """
        return self._user_name_map.get(user_id)

    def get_stroke(self, bell: Bell) -> Optional[Stroke]:
        """Returns the stroke of a given bell."""
        if bell.index >= len(self._bell_state) or bell.index < 0:
            self.logger.error(f"Bell {bell} not in tower")
            return None
        return self._bell_state[bell.index]

    def make_call(self, call: str) -> None:
        """Broadcasts a given call to the other users of the tower."""
        self.logger.info(f"EMIT: Calling '{call}'")
        self._emit("c_call", {"call": call})

    def set_is_ringing(self, value: bool) -> None:
        """
        Only used by server mode, which Ringing Room's API 2.0 has no place for (the server's own
        simulator says whether it is ringing), so this does nothing.
        """
        self.logger.debug(f"Not telling RR clients to set is_ringing to {value}: no such message in API 2.0")

    def emit_roll_call(self, instance_id: int) -> None:  # pylint: disable=unused-argument
        """
        Only used by server mode, which API 2.0 has no place for (it has no roll call), so this does
        nothing.
        """
        self.logger.debug("Not replying to roll call: no such message in API 2.0")

    def wait_loaded(self) -> None:
        """
        Pause the thread until the server has sent everything about the tower.  Raises
        `RingingRoomTowerConnectError` (with the server's reason, if it gave one) if it won't let us in.
        """
        if self._ws is None:
            raise RingingRoomTowerConnectError("Not Connected")

        # The join burst ends with Wheatley's own `s_user_entered`, after every assignment
        waited = 0.0
        while not self._loaded.is_set() and not self._closed.is_set() and waited < LOAD_TIMEOUT:
            self._loaded.wait(timeout=0.05)
            waited += 0.05
        if self._loaded.is_set():
            return
        raise RingingRoomTowerConnectError(self.closed_reason or "Not received tower state from Ringing Room")

    def _connect(self) -> None:
        """Opens the WebSocket, starts reading it, and joins the tower as a bot."""
        try:
            self._ws = websocket.create_connection(self._ws_url, timeout=CONNECT_TIMEOUT)
        except websocket.WebSocketBadStatusException as e:
            if e.status_code == 404:
                raise TowerNotFoundError(self.tower_id, self._ws_url) from e
            if e.status_code == 503:
                raise RingingRoomTowerConnectError("The server is restarting.  Try again in a minute.") from e
            raise InvalidURLError(self._ws_url) from e
        except (websocket.WebSocketException, OSError) as e:
            raise InvalidURLError(self._ws_url) from e
        self._ws.settimeout(None)
        self.logger.debug(f"Connected to {self._ws_url}")

        self._thread = threading.Thread(target=self._read_messages, name="tower-socket", daemon=True)
        self._thread.start()

        self._join_tower()

    def _join_tower(self) -> None:
        """Joins the tower as a bot, which is how Ringing Room lets a client ring without logging in."""
        self.logger.info(f"EMIT: Joining tower {self.tower_id}")
        payload: Dict[str, Any] = {"role": "bot"}
        if self._name is not None:
            payload["name"] = self._name
        self._emit("c_join", payload)

    def _read_messages(self) -> None:
        """Reads the socket until it closes, handling each message.  Runs on its own thread."""
        try:
            while True:
                ws = self._ws
                if ws is None:
                    break
                message = ws.recv()
                if message == "" or message is None:
                    break  # closed
                if isinstance(message, str):  # (a binary frame is never a message)
                    self._on_message(message)
        except (websocket.WebSocketException, OSError) as e:
            self.logger.debug(f"Connection ended: {e}")
        finally:
            self._closed.set()
            self.logger.info("The connection to Ringing Room has closed")
            for callback in self.invoke_on_close:
                callback()

    def _on_message(self, text: str) -> None:
        """Handles one message from the server: a JSON object with an `event` and a `payload`."""
        try:
            message = json.loads(text)
            event: str = message["event"]
            payload: JSON = message.get("payload") or {}
        except (ValueError, KeyError, TypeError, AttributeError):
            self.logger.warning(f"RECEIVED: Unreadable message: {text[:200]}")
            return

        handlers: Dict[str, Callable[[JSON], None]] = {
            "s_bell_rung": self._on_bell_rung,
            "s_global_state": self._on_global_bell_state,
            "s_user_entered": self._on_user_entered,
            "s_set_userlist": self._on_user_list,
            "s_size_change": self._on_size_change,
            "s_assign_user": self._on_assign_user,
            "s_host_mode": self._on_host_mode,
            "s_call": self._on_call,
            "s_user_left": self._on_user_leave,
            "s_wheatley_setting": self._on_setting_change,
            "s_wheatley_row_gen": self._on_row_gen_change,
            "s_error": self._on_error,
        }
        handler = handlers.get(event)
        if handler is None:
            self.logger.debug(f"RECEIVED: Ignoring '{event}'")
            return
        try:
            handler(payload)
        except Exception as e:  # pylint: disable=broad-except
            # A message that surprises us mustn't stop us reading the ones after it
            self.logger.error(f"Couldn't handle '{event}' {payload}: {e!r}")

    # The values in data could have any types, so we don't need any type checking here.
    def _on_error(self, data: JSON) -> None:
        """Called when the server refuses something, or tells us it is about to close the connection."""
        reason: str = data.get("reason", "")
        message: str = data.get("message", "")
        command = data.get("command")
        if reason in FATAL_REASONS:
            self.logger.error(f"RECEIVED: {message}")
            self._fatal_error = (reason, message)
        elif reason == "rate_limited":
            # Dropped, and if this goes on the server closes the connection and says so
            self.logger.warning(f"RECEIVED: {message}")
            self._last_rate_limit_message = message
        elif reason == "bot_bell_assigned":
            # Someone has been given a bell since we last heard; the assignment is on its way
            self.logger.info(f"RECEIVED: Couldn't ring: {message}")
        else:
            self.logger.warning(f"RECEIVED: {command} was refused ({reason}): {message}")

    def _on_setting_change(self, data: JSON) -> None:
        # Log a message (to info if the setting change is used, debug otherwise)
        is_ignored = len(self.invoke_on_setting_change) == 0
        log_message = f"RECEIVED: Settings changed: {data}{' (ignoring)' if is_ignored else ''}"
        if is_ignored:
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)

        for key, value in data.items():
            for callback in self.invoke_on_setting_change:
                callback(key, value)

    def _on_row_gen_change(self, data: JSON) -> None:
        # Log a message (to info if the setting change is used, debug otherwise)
        is_ignored = len(self.invoke_on_row_gen_change) == 0
        log_message = f"RECEIVED: Row gen changed: {data}{' (ignoring)' if is_ignored else ''}"
        if is_ignored:
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)

        for callback in self.invoke_on_row_gen_change:
            callback(data)

    def _on_user_leave(self, data: JSON) -> None:
        # Unpack the data and assign it the expected types
        user_id_that_left: int = data["user_id"]

        if data.get("kicked") and user_id_that_left == self._my_user_id:
            self.logger.error("RECEIVED: Wheatley has been kicked from the tower")
            self._fatal_error = ("kicked", "Wheatley was kicked from the tower.")
            return

        bells_unassigned: List[Bell] = []

        # Unassign all instances of that user
        with self._assignment_lock:
            for bell, user in self._assigned_users.items():
                if user == user_id_that_left:
                    bells_unassigned.append(bell)
            for bell in bells_unassigned:
                del self._assigned_users[bell]

        user_name_that_left = self._user_name_map.get(user_id_that_left)
        self.logger.info(
            f"RECEIVED: User #{user_id_that_left}:'{user_name_that_left}' left from bells {bells_unassigned}."
        )

    def _on_user_entered(self, data: JSON) -> None:
        """Called when the server receives a uew user so we can update our user list."""
        # Unpack the data and assign it expected types
        user_id: int = data["user_id"]
        username: str = data["username"]
        # Add the new user to the user list, so we can match up their ID with their username
        self._user_name_map[user_id] = username
        # The first of these is our own, which ends the join burst (the others are only sent afterwards)
        if self._my_user_id is None:
            self._my_user_id = user_id
            self.logger.info(f"RECEIVED: Joined as '{username}' (user #{user_id})")
            self._loaded.set()

    def _on_user_list(self, user_list: JSON) -> None:
        """Called when the server broadcasts a user list when Wheatley joins a tower."""
        for user in user_list["user_list"]:
            # Unpack the data and assign it expected types
            user_id: int = user["user_id"]
            username: str = user["username"]
            self._user_name_map[user_id] = username

    def _on_bell_rung(self, data: JSON) -> None:
        """Callback called when the client receives a signal that a bell has been rung."""
        # Ringing a bell turns it over, and the message only says which one rang
        who_rang = Bell.from_number(data["who_rang"])
        if who_rang.index >= len(self._bell_state):
            self.logger.warning(f"Bell {who_rang} rang, but the tower only has {self.number_of_bells} bells.")
            return
        self._bell_state[who_rang.index] = self._bell_state[who_rang.index].opposite()
        self.logger.debug(f"RECEIVED: Bells '{''.join([s.char() for s in self._bell_state])}'")
        # Run the callbacks, which want the stroke the bell is now on
        for bell_ring_callback in self.invoke_on_bell_rung:
            bell_ring_callback(who_rang, self._bell_state[who_rang.index])

    def _on_global_bell_state(self, data: JSON) -> None:
        """
        Callback called when receiving an update to the global tower state: when we join, after
        every resize, and when the server finds that a bell was rung on the wrong stroke.
        """
        global_bell_state: List[bool] = data["global_bell_state"]
        self._bell_state = [Stroke(x) for x in global_bell_state]
        self.logger.debug(f"RECEIVED: Bells '{''.join([s.char() for s in self._bell_state])}'")
        for invoke_callback in self.invoke_on_reset:
            invoke_callback()

    def _on_size_change(self, data: JSON) -> None:
        """Callback called when the number of bells in the room changes."""
        new_size: int = data["size"]
        if new_size != self.number_of_bells:
            # Remove the bells that have gone (so that returning to a stage doesn't make Wheatley think
            # they are still assigned)
            with self._assignment_lock:
                self._assigned_users = {
                    bell: user for (bell, user) in self._assigned_users.items() if bell.number <= new_size
                }
            # The server follows every resize with the state of the bells
            self.logger.info(f"RECEIVED: New tower size '{new_size}'")

    def _on_host_mode(self, data: JSON) -> None:
        """Callback called when host mode is turned on or off, and when we join."""
        self._host_mode = bool(data["new_mode"])
        self.logger.info(f"RECEIVED: Host mode is {'on' if self._host_mode else 'off'}")

    def _on_assign_user(self, data: JSON) -> None:
        """Callback called when a bell assignment is changed."""
        raw_bell: int = data["bell"]
        bell: Bell = Bell.from_number(raw_bell)
        user: Optional[int] = data["user"] or None

        assert (
            isinstance(user, int) or user is None
        ), f"User ID {user} is not an integer (it has type {type(user)})."

        with self._assignment_lock:
            if user is None:
                self.logger.info(f"RECEIVED: Unassigned bell '{bell}'")
                self._assigned_users.pop(bell, None)
            else:
                self._assigned_users[bell] = user
                self.logger.info(f"RECEIVED: Assigned bell '{bell}' to '{self.user_name_from_id(user)}'")

    def _on_call(self, data: Dict[str, str]) -> None:
        """Callback called when a call is made."""
        call = data["call"]
        self.logger.info(f"RECEIVED: Call '{call}'")

        found_callback = False
        for call_callback in self.invoke_on_call.get(call, []):
            call_callback()
            found_callback = True
        if not found_callback:
            self.logger.debug(f"No callback found for '{call}'")

    def _emit(self, event: str, payload: Any) -> None:
        """Send a message to the server."""
        if self._ws is None or self._closed.is_set():
            raise SocketClientError("Not Connected")

        self._ws.send(json.dumps({"event": event, "payload": payload}))


class SocketClientError(Exception):
    """Errors related to the WebSocket"""
