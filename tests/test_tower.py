"""Tests for the connection to Ringing Room: how Wheatley reads the server's messages and what he sends."""

import json
from typing import Any, Dict, List, Optional
from unittest import TestCase

import websocket  # type: ignore

from wheatley.bell import Bell
from wheatley.server_url import InvalidURLError, TowerNotFoundError, websocket_url
from wheatley.stroke import BACKSTROKE, HANDSTROKE
from wheatley.tower import RingingRoomTower, RingingRoomTowerConnectError


class FakeSocket:
    """Stands in for the WebSocket: records what is sent, and hands over what the test queues."""

    def __init__(self) -> None:
        self.sent: List[Dict[str, Any]] = []
        self.closed = False

    def send(self, text: str) -> None:
        self.sent.append(json.loads(text))

    def close(self) -> None:
        self.closed = True


def message(event: str, **payload: Any) -> str:
    return json.dumps({"event": event, "payload": payload})


def burst(tower: RingingRoomTower, size: int = 6, me: int = -2, assignments: Optional[Dict[int, Any]] = None):
    """Delivers a server's join burst to `tower`, ending (as the server does) with its own s_user_entered."""
    users = [{"user_id": -1, "username": "Wheatley", "badge": None}, {"user_id": 7, "username": "alice"}]
    users.append({"user_id": me, "username": "Wheatley (CLI)", "badge": "badge-bot.png"})
    tower._on_message(message("s_set_userlist", user_list=users))
    tower._on_message(message("s_size_change", size=size))
    tower._on_message(message("s_global_state", global_bell_state=[True] * size))
    for bell in range(1, size + 1):
        tower._on_message(message("s_assign_user", bell=bell, user=(assignments or {}).get(bell, "")))
    tower._on_message(message("s_set_observers", observers=0))
    tower._on_message(message("s_user_entered", user_id=me, username="Wheatley (CLI)", badge="badge-bot.png"))


def make_tower(name: Optional[str] = None) -> RingingRoomTower:
    tower = RingingRoomTower(123456789, "https://example.org/", name)
    tower._ws = FakeSocket()  # pylint: disable=protected-access
    return tower


def sent(tower: RingingRoomTower) -> List[Dict[str, Any]]:
    return tower._ws.sent  # type: ignore # pylint: disable=protected-access


class WebSocketUrlTests(TestCase):
    def test_http_address(self) -> None:
        for given, expected in [
            ("https://ringingroom.com", "wss://ringingroom.com/ws/123"),
            ("https://ringingroom.com/", "wss://ringingroom.com/ws/123"),
            ("ringingroom.com", "wss://ringingroom.com/ws/123"),
            ("https://na.ringingroom.com/123456789", "wss://na.ringingroom.com/ws/123"),
            ("http://localhost:8080", "ws://localhost:8080/ws/123"),
        ]:
            with self.subTest(given):
                self.assertEqual(websocket_url(123, given), expected)

    def test_no_host(self) -> None:
        with self.assertRaises(InvalidURLError):
            websocket_url(123, "https://")


class JoinTests(TestCase):
    def test_joins_as_a_bot_with_no_token_and_no_tower_id(self) -> None:
        tower = make_tower()
        tower._join_tower()  # pylint: disable=protected-access
        self.assertEqual(sent(tower), [{"event": "c_join", "payload": {"role": "bot"}}])

    def test_joins_with_a_name(self) -> None:
        tower = make_tower("Fred's Wheatley")
        tower._join_tower()  # pylint: disable=protected-access
        self.assertEqual(sent(tower)[0]["payload"], {"role": "bot", "name": "Fred's Wheatley"})

    def test_the_burst_loads_the_tower_and_the_last_message_is_our_own_entry(self) -> None:
        tower = make_tower()
        resets: List[int] = []
        tower.invoke_on_reset.append(lambda: resets.append(tower.number_of_bells))
        burst(tower, size=6)
        tower.wait_loaded()  # returns, rather than timing out
        self.assertEqual(tower.number_of_bells, 6)
        self.assertEqual(tower._my_user_id, -2)  # pylint: disable=protected-access
        self.assertEqual(tower.user_name_from_id(7), "alice")
        self.assertEqual(resets, [6])

    def test_wait_loaded_stops_when_the_server_refuses_us(self) -> None:
        tower = make_tower("x" * 30)
        tower._on_message(  # pylint: disable=protected-access
            message("s_error", command="c_join", reason="invalid_name", message="That name can't be used.")
        )
        tower._closed.set()  # pylint: disable=protected-access
        with self.assertRaises(RingingRoomTowerConnectError) as raised:
            tower.wait_loaded()
        self.assertEqual(str(raised.exception), "That name can't be used.")
        self.assertEqual(tower.closed_reason, "That name can't be used.")


class RingingTests(TestCase):
    def test_which_bells_to_ring_with_nobody_assigned_to_us(self) -> None:
        tower = make_tower()
        burst(tower, assignments={1: 7, 2: -1})  # alice has the treble, the simulator the 2
        self.assertEqual(
            [tower.should_ring(Bell.from_number(n)) for n in range(1, 7)],
            [False, False, True, True, True, True],
        )

    def test_which_bells_to_ring_when_assigned_some(self) -> None:
        tower = make_tower()
        burst(tower, assignments={3: -2, 4: -2, 5: 7})
        self.assertEqual(
            [tower.should_ring(Bell.from_number(n)) for n in range(1, 7)],
            [False, False, True, True, False, False],
        )

    def test_assignments_change_the_answer_as_they_come_and_go(self) -> None:
        tower = make_tower()
        burst(tower)
        self.assertTrue(tower.should_ring(Bell.from_number(1)))
        tower._on_message(message("s_assign_user", bell=4, user=-2))  # pylint: disable=protected-access
        self.assertFalse(tower.should_ring(Bell.from_number(1)))
        self.assertTrue(tower.should_ring(Bell.from_number(4)))
        tower._on_message(message("s_assign_user", bell=4, user=""))  # pylint: disable=protected-access
        self.assertTrue(tower.should_ring(Bell.from_number(1)))

    def test_a_person_leaving_frees_their_bells(self) -> None:
        tower = make_tower()
        burst(tower, assignments={1: 7})
        self.assertFalse(tower.should_ring(Bell.from_number(1)))
        tower._on_message(  # pylint: disable=protected-access
            message("s_user_left", user_id=7, username="alice")
        )
        self.assertTrue(tower.should_ring(Bell.from_number(1)))

    def test_in_host_mode_only_our_own_bells_are_rung_even_if_we_have_none(self) -> None:
        tower = make_tower()
        burst(tower, assignments={1: 7})
        self.assertTrue(tower.should_ring(Bell.from_number(2)))  # not in host mode: any bell nobody has
        tower._on_message(message("s_host_mode", new_mode=True))  # pylint: disable=protected-access
        self.assertEqual([tower.should_ring(Bell.from_number(n)) for n in range(1, 7)], [False] * 6)
        tower._on_message(message("s_assign_user", bell=4, user=-2))  # pylint: disable=protected-access
        self.assertEqual(
            [tower.should_ring(Bell.from_number(n)) for n in range(1, 7)],
            [False, False, False, True, False, False],
        )
        tower._on_message(message("s_host_mode", new_mode=False))  # pylint: disable=protected-access
        self.assertFalse(tower.should_ring(Bell.from_number(2)))  # we hold bell 4, so only that one
        tower._on_message(message("s_assign_user", bell=4, user=""))  # pylint: disable=protected-access
        self.assertTrue(tower.should_ring(Bell.from_number(2)))

    def test_joining_a_host_mode_tower_starts_in_host_mode(self) -> None:
        tower = make_tower()
        tower._on_message(message("s_host_mode", new_mode=True))  # pylint: disable=protected-access
        burst(tower)
        self.assertFalse(tower.should_ring(Bell.from_number(3)))

    def test_ringing_sends_the_bell_and_stroke_and_no_tower_id(self) -> None:
        tower = make_tower()
        burst(tower)
        self.assertTrue(tower.ring_bell(Bell.from_number(3), HANDSTROKE))
        self.assertEqual(sent(tower), [{"event": "c_bell_rung", "payload": {"bell": 3, "stroke": True}}])

    def test_wont_ring_a_bell_on_the_wrong_stroke(self) -> None:
        tower = make_tower()
        burst(tower)
        self.assertFalse(tower.ring_bell(Bell.from_number(3), BACKSTROKE))
        self.assertEqual(sent(tower), [])

    def test_a_bell_rung_turns_over_the_bell_the_server_names(self) -> None:
        tower = make_tower()
        burst(tower, size=4)
        heard: List[Any] = []
        tower.invoke_on_bell_rung.append(lambda bell, stroke: heard.append((bell.number, stroke)))
        tower._on_message(message("s_bell_rung", who_rang=2))  # pylint: disable=protected-access
        # The callback gets the stroke the bell is now on, and only that bell turned
        self.assertEqual(heard, [(2, BACKSTROKE)])
        self.assertEqual(tower.get_stroke(Bell.from_number(2)), BACKSTROKE)
        self.assertEqual(tower.get_stroke(Bell.from_number(1)), HANDSTROKE)
        tower._on_message(message("s_bell_rung", who_rang=2))  # pylint: disable=protected-access
        self.assertEqual(tower.get_stroke(Bell.from_number(2)), HANDSTROKE)

    def test_the_servers_state_replaces_ours_when_it_finds_us_out_of_step(self) -> None:
        tower = make_tower()
        burst(tower, size=4)
        tower._on_message(
            message("s_global_state", global_bell_state=[False, True, True, False])
        )  # pylint: disable=protected-access
        self.assertEqual(
            [tower.get_stroke(Bell.from_number(n)) for n in range(1, 5)],
            [BACKSTROKE, HANDSTROKE, HANDSTROKE, BACKSTROKE],
        )

    def test_a_resize_drops_assignments_to_bells_that_are_gone(self) -> None:
        tower = make_tower()
        burst(tower, size=8, assignments={7: -2})
        self.assertFalse(tower.should_ring(Bell.from_number(1)))
        tower._on_message(message("s_size_change", size=6))  # pylint: disable=protected-access
        tower._on_message(
            message("s_global_state", global_bell_state=[True] * 6)
        )  # pylint: disable=protected-access
        self.assertTrue(tower.should_ring(Bell.from_number(1)))  # no bell of ours is left

    def test_calls_are_sent_without_a_tower_id(self) -> None:
        tower = make_tower()
        tower.make_call("Stand next")
        self.assertEqual(sent(tower), [{"event": "c_call", "payload": {"call": "Stand next"}}])

    def test_calls_made_by_others_reach_their_callbacks(self) -> None:
        tower = make_tower()
        heard: List[str] = []
        tower.invoke_on_call["Look to"].append(lambda: heard.append("look to"))
        tower._on_message(message("s_call", call="Look to"))  # pylint: disable=protected-access
        tower._on_message(message("s_call", call="Bob"))  # pylint: disable=protected-access
        self.assertEqual(heard, ["look to"])


class ServerMessageTests(TestCase):
    def test_being_kicked_ends_the_session_with_a_reason(self) -> None:
        tower = make_tower()
        burst(tower)
        tower._on_message(
            message("s_user_left", user_id=-2, username="Wheatley (CLI)", kicked=True)
        )  # pylint: disable=protected-access
        self.assertEqual(tower.closed_reason, "Wheatley was kicked from the tower.")

    def test_someone_else_being_kicked_does_not(self) -> None:
        tower = make_tower()
        burst(tower, assignments={1: 7})
        tower._on_message(
            message("s_user_left", user_id=7, username="alice", kicked=True)
        )  # pylint: disable=protected-access
        self.assertIsNone(tower.closed_reason)
        self.assertTrue(tower.should_ring(Bell.from_number(1)))

    def test_refusals_that_end_the_connection_are_remembered(self) -> None:
        for reason in ["bots_not_permitted", "server_restarting", "invalid_name"]:
            with self.subTest(reason):
                tower = make_tower()
                tower._on_message(
                    message("s_error", command=None, reason=reason, message=reason + "!")
                )  # pylint: disable=protected-access
                self.assertEqual(tower.closed_reason, reason + "!")

    def test_being_closed_for_sending_too_fast_is_explained(self) -> None:
        tower = make_tower()
        msg = "Too many messages, too fast. The connection is being closed."
        tower._on_message(
            message("s_error", command="c_bell_rung", reason="rate_limited", message=msg)
        )  # pylint: disable=protected-access
        self.assertIsNone(tower.closed_reason)  # still connected: only dropped
        tower._closed.set()  # pylint: disable=protected-access
        self.assertEqual(tower.closed_reason, msg)

    def test_other_refusals_do_not_end_anything(self) -> None:
        for reason in ["bot_bell_assigned", "bot_call_not_permitted", "not_permitted_for_bots"]:
            with self.subTest(reason):
                tower = make_tower()
                tower._on_message(
                    message("s_error", command="c_bell_rung", reason=reason, message="no")
                )  # pylint: disable=protected-access
                self.assertIsNone(tower.closed_reason)

    def test_messages_that_make_no_sense_are_ignored_not_fatal(self) -> None:
        tower = make_tower()
        burst(tower, size=4)
        for text in ["", "not json", "[]", '{"payload": {}}', message("s_bell_rung"), message("s_who_knows")]:
            tower._on_message(text)  # pylint: disable=protected-access
        self.assertEqual(tower.number_of_bells, 4)


class ConnectionTests(TestCase):
    """The real socket code, against a server that is not there."""

    def test_unreachable_server(self) -> None:
        tower = RingingRoomTower(123, "http://127.0.0.1:1")  # nothing listens on port 1
        with self.assertRaises(InvalidURLError):
            with tower:
                pass

    def test_a_refused_upgrade_for_an_unknown_tower(self) -> None:
        tower = RingingRoomTower(123, "http://127.0.0.1:1")
        original = websocket.create_connection

        def refuse(*_args: Any, **_kwargs: Any) -> Any:
            raise websocket.WebSocketBadStatusException("Handshake status %d %s", 404, "Not Found")

        websocket.create_connection = refuse
        try:
            with self.assertRaises(TowerNotFoundError):
                with tower:
                    pass
        finally:
            websocket.create_connection = original

    def test_a_server_shutting_down_gets_a_clear_message(self) -> None:
        tower = RingingRoomTower(123, "http://127.0.0.1:1")
        original = websocket.create_connection

        def refuse(*_args: Any, **_kwargs: Any) -> Any:
            raise websocket.WebSocketBadStatusException("Handshake status %d %s", 503, "Service Unavailable")

        websocket.create_connection = refuse
        try:
            with self.assertRaises(RingingRoomTowerConnectError):
                with tower:
                    pass
        finally:
            websocket.create_connection = original
