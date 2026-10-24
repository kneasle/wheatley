"""
A module to turn the address a user gives for a Ringing Room server (and a tower id) into the URL of the
tower's WebSocket.
"""

from urllib.parse import urlsplit


class TowerNotFoundError(ValueError):
    """An error class created whenever the user inputs an incorrect room id."""

    def __init__(self, tower_id: int, url: str) -> None:
        super().__init__()

        self._id = tower_id
        self._url = url

    def __str__(self) -> str:
        return f"Tower {self._id} not found at '{self._url}'."


class InvalidURLError(Exception):
    """An error class created whenever the user inputs a URL that is invalid."""

    def __init__(self, url: str) -> None:
        super().__init__()

        self._url = url

    def __str__(self) -> str:
        return f"Unable to make a connection to '{self._url}'."


def _fix_url(url: str) -> str:
    """Add 'https://' to the start of a URL if necessary"""
    return url if url.startswith("http") else "https://" + url


def websocket_url(tower_id: int, unfixed_http_server_url: str) -> str:
    """
    The URL of a tower's WebSocket (`wss://<host>/ws/<tower id>`) on the given server, which is given as
    the address people put in their browser (the scheme is optional, and any path or trailing slash is
    ignored).  Raises `InvalidURLError` if there is no host in it.
    """
    http_server_url = _fix_url(unfixed_http_server_url)
    parts = urlsplit(http_server_url)
    if not parts.netloc:
        raise InvalidURLError(http_server_url)
    scheme = "wss" if parts.scheme == "https" else "ws"
    return f"{scheme}://{parts.netloc}/ws/{tower_id}"
