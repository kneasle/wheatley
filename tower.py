import collections
import logging
from time import sleep
from typing import Optional, Callable, Dict, List, Any

import socketio

from bell import Bell


class RingingRoomTower:
    logger_name = "TOWER"

    def __init__(self, tower_id: int, url: str):
        self.tower_id = tower_id
        self.logger = logging.getLogger(self.logger_name)
        self._bell_state = []
        self._assigned_users = {}

        self.invoke_on_call: Dict[str, List[Callable[[], Any]]] = collections.defaultdict(list)
        self.invoke_on_reset: List[Callable[[], Any]] = []
        self.invoke_on_bell_rung: List[Callable[[int, bool], Any]] = []

        self._url = url
        self._socket_io_client: Optional[socketio.Client] = None

    def __enter__(self):
        self.logger.debug("ENTER")
        if self._socket_io_client is not None:
            raise Exception("Trying to connect twice")
        self._create_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug("EXIT")
        if self._socket_io_client:
            self.logger.info("Disconnect")
            self._socket_io_client.disconnect()
            self._socket_io_client = None

    @property
    def number_of_bells(self):
        return len(self._bell_state)

    def ring_bell(self, bell: Bell, handstroke: bool):
        try:
            stroke = self.get_stroke(bell)
            if stroke != handstroke:
                self.logger.error(f"Bell {bell} on opposite stroke")
                return False
            self._emit("c_bell_rung", {"bell": bell.number, "stroke": stroke, "tower_id": self.tower_id}, "")
            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def user_controlled(self, bell: Bell):
        return self._assigned_users.get(bell, "") != ""

    def get_stroke(self, bell: Bell):
        if bell.index >= len(self._bell_state) or bell.index < 0:
            self.logger.error(f"Bell {bell} not in tower")
            return None
        return self._bell_state[bell.index]

    def make_call(self, call: str):
        self._emit("c_call", {"call": call, "tower_id": self.tower_id}, f"Call '{call}'")

    def set_at_hand(self):
        self._emit("c_set_bells", {"tower_id": self.tower_id}, f"Set at hand")

    def set_number_of_bells(self, number: int):
        self._emit("c_size_change", {"new_size": number, "tower_id": self.tower_id}, f"Set number of bells '{number}'")

    def wait_loaded(self):
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
        self._socket_io_client = socketio.Client()
        self._socket_io_client.connect(self._url)
        self.logger.info(f"Connected to {self._url}")
        self._join_tower()

        self._socket_io_client.on("s_bell_rung", self._on_bell_rung)
        self._socket_io_client.on("s_global_state", self._on_global_bell_state)
        self._socket_io_client.on("s_size_change", self._on_size_change)
        self._socket_io_client.on("s_assign_user", self._on_assign_user)
        self._socket_io_client.on("s_call", self._on_call)

        self._request_global_state()

    def _join_tower(self):
        self._emit("c_join", {"anonymous_user": True, "tower_id": self.tower_id}, f"Joining tower {self.tower_id}")

    def _request_global_state(self):
        self._emit('c_request_global_state', {"tower_id": self.tower_id}, "Request state")

    def _emit(self, event: str, data, message: str):
        if self._socket_io_client is None:
            raise Exception("Not Connected")

        self._socket_io_client.emit(event, data)

        if message:
            self.logger.info(f"EMIT: {message}")

    def _on_bell_rung (self, data):
        self._on_global_bell_state(data)

        who_rang = Bell.from_number(data ["who_rang"])
        for bell_ring_callback in self.invoke_on_bell_rung:
            bell_ring_callback(who_rang, self.get_stroke(who_rang))

    def _on_global_bell_state (self, data):
        bell_state = data["global_bell_state"]
        self._bell_state = bell_state

        self.logger.debug(f"RECEIVED: Bells '{['H' if x else 'B' for x in bell_state]}'")

    def _on_size_change(self, data):
        new_size = data["size"]
        if new_size != self.number_of_bells:
            self._assigned_users = {}
            self._bell_state = self._bells_set_at_hand(new_size)
            self.logger.info(f"RECEIVED: New tower size '{new_size}'")
            for invoke_callback in self.invoke_on_reset:
                invoke_callback()

    def _on_assign_user(self, data):
        bell = Bell.from_number(data["bell"])
        user = data["user"]
        self._assigned_users[bell] = user
        self.logger.info(f"RECEIVED: Assigned bell '{bell}' to '{user or 'BOT'}'")

    def _on_call(self, data):
        call = data["call"]
        self.logger.info (f"RECEIVED: Call '{call}'")

        found_callback = False
        for call_callback in self.invoke_on_call.get(call, []):
            call_callback()
            found_callback = True
        if not found_callback:
            self.logger.warning (f"No callback found for '{call}'")

    @staticmethod
    def _bells_set_at_hand(number: int):
        return [True for _ in range(number)]
