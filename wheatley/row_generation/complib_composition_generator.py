""" Contains the RowGenerator subclass for generating rows from a CompLib composition. """

import json
from typing import Dict, Optional, List, Tuple
from urllib.parse import urlparse

import requests

from wheatley.aliases import Row
from wheatley.stroke import Stroke
from wheatley.bell import Bell
from .row_generator import RowGenerator


class PrivateCompError(ValueError):
    """An error class thrown when a user tries to access a private CompLib composition."""

    def __init__(self, comp_id: int) -> None:
        super().__init__()

        self._comp_id = comp_id

    def __str__(self) -> str:
        return f"Composition with ID {self._comp_id} is private."


class InvalidCompError(ValueError):
    """An error class thrown when a user tries to access an invalid CompLib composition."""

    def __init__(self, comp_id: int) -> None:
        super().__init__()

        self._comp_id = comp_id

    def __str__(self) -> str:
        return f"Composition with ID {self._comp_id} is does not exist."


class InvalidComplibURLError(Exception):
    """An error class thrown when a user inputs an invalid complib comp URL."""

    def __init__(self, url: str, error: str) -> None:
        super().__init__()

        self._url = url
        self._error = error

    def __str__(self) -> str:
        return f"Invalid CompLib URL '{self._url}': {self._error}"


# The 'removeprefix' function from Python 3.9
def removeprefix(string: str, prefix: str) -> str:
    """Removes a prefix from a given string if it exists."""
    if string.startswith(prefix):
        return string[len(prefix) :]
    return string[:]


def parse_arg(arg: str) -> Tuple[int, Optional[str], Optional[int]]:
    """Parses a URL or a plain ID into a tuple of (ID, access key, substituted method ID)."""
    # === CONVERT ID NUMBER INTO A NORMALISED URL ===
    # If the arg doesn't contain 'complib.org', we assume it's simply an ID (perhaps with an access
    # key) and so turn it into a URL
    if "complib.org" in arg:
        url = arg
    else:
        url = "https://complib.org/composition/" + arg
    # Make sure that the URL starts with `https://`
    if not url.startswith("http"):
        url = "https://" + url

    # === PARSE URL, AND SPLIT PATH SEGMENTS ===
    # `url` looks like a URL, so try to parse it
    parsed_url = urlparse(url)
    # Naively split the URL path with `/`s.  This is technically wrong because it doesn't handle
    # escaping properly, but we don't worry about that because CompLib URLs shouldn't have any
    # escaped `/`s anyway.
    path_segs = parsed_url.path.split("/")

    # === PARSE COMP ID FROM PATH SEGMENTS ===
    # Check that we have an absolute path, and remove the '' at the front of the list of path
    # segments
    assert path_segs[0] == ""
    path_segs = path_segs[1:]
    # Raise helpful error messages if obvious things are wrong (these errors can't happen if the
    # user used a straight ID)
    if len(path_segs) <= 1:
        raise InvalidComplibURLError(url, "URL needs more path segments.")
    if path_segs[0] != "composition":
        raise InvalidComplibURLError(url, "Not a composition.")
    # Parse the 2nd URL segment into the comp ID
    try:
        comp_id = int(path_segs[1])
    except ValueError as e:
        raise InvalidComplibURLError(url, f"Composition ID '{path_segs[1]}' is not a number.") from e

    # === PARSE ACCESS KEY FROM THE QUERY STRING ===
    access_key = None
    substituted_method_id = None
    for q in parsed_url.query.split("&"):
        parts = q.split("=")
        if len(parts) != 2:
            continue
        if parts[0] == "accessKey":
            access_key = parts[1]
        if parts[0] == "substitutedmethodid":
            try:
                substituted_method_id = int(parts[1])
            except ValueError as e:
                raise InvalidComplibURLError(
                    url, f"Substituted method ID '{parts[1]}' is not a number."
                ) from e

    return (comp_id, access_key, substituted_method_id)


class ComplibCompositionGenerator(RowGenerator):
    """The RowGenerator subclass for generating rows from a CompLib composition."""

    complib_url = "https://api.complib.org/composition/"

    def __init__(
        self, comp_id: int, access_key: Optional[str] = None, substituted_method_id: Optional[int] = None
    ) -> None:
        def process_call_string(calls: str) -> List[str]:
            """Parse a sequence of calls, and remove 'Stand'."""
            stripped_calls = [x.strip() for x in calls.split(";")]
            return [c for c in stripped_calls if c != "Stand"]

        # Generate URL from the params
        query_sections: List[str] = []
        if access_key:
            query_sections.append(f"accessKey={access_key}")
        if substituted_method_id:
            query_sections.append(f"substitutedmethodid={substituted_method_id}")
        url = self.complib_url + str(comp_id) + "/rows"
        if query_sections:
            url += "?" + "&".join(query_sections)
        # Create an HTTP request for the rows, and deal with potential error codes
        request_rows = requests.get(url, timeout=30)
        if request_rows.status_code == 404:
            raise InvalidCompError(comp_id)
        if request_rows.status_code == 403:
            raise PrivateCompError(comp_id)
        request_rows.raise_for_status()
        # Parse the request responses as JSON
        response_rows = json.loads(request_rows.text)
        unparsed_rows = response_rows["rows"]
        # Determine the start row of the composition
        num_starting_rounds = 0
        while unparsed_rows[num_starting_rounds][0] == unparsed_rows[0][0]:
            num_starting_rounds += 1
        self._start_stroke = Stroke.from_index(num_starting_rounds)
        # Derive the rows, calls and stage from the JSON response
        loaded_rows: List[Tuple[Row, List[str]]] = [
            (Row([Bell.from_str(bell) for bell in row]), [] if calls == "" else process_call_string(calls))
            for row, calls, _property_bitmap in unparsed_rows
        ]
        # Convert these parsed rows into a format that we can read more easily when ringing.  I.e.
        # load the non-rounds rows as-is, but keep the calls that should be called in rounds
        self.loaded_rows = loaded_rows[num_starting_rounds:]
        self._early_calls = {
            num_starting_rounds - i: calls
            for i, (_row, calls) in enumerate(loaded_rows[:num_starting_rounds])
            if calls != []
        }
        # Set the variables from which the summary string is generated
        self.comp_id = comp_id
        self.comp_title = response_rows["title"]
        self.is_comp_private = access_key is not None
        # Propogate the initialisation up to the parent class
        super().__init__(response_rows["stage"])

    @classmethod
    def from_arg(cls, arg: str) -> "ComplibCompositionGenerator":
        """Generates a ComplibCompositionGenerator from either a URL or the ID of a comp."""
        comp_id, access_key, substituted_method_id = parse_arg(arg)
        return cls(comp_id, access_key, substituted_method_id)

    def summary_string(self) -> str:
        """Returns a short string summarising the RowGenerator."""
        return f"{'private ' if self.is_comp_private else ''}comp #{self.comp_id}: {self.comp_title}"

    def _gen_row_and_calls(self, _previous_row: Row, _stroke: Stroke, index: int) -> Tuple[Row, List[str]]:
        if index < len(self.loaded_rows):
            return self.loaded_rows[index]
        return (self.rounds(), [])

    def _gen_row(self, previous_row: Row, stroke: Stroke, index: int) -> Row:
        # Technically, this should be unreachable, but Python doesn't have an error for that (I miss
        # Rust's `unreachable!` macro)
        raise NotImplementedError()

    def start_stroke(self) -> Stroke:
        """
        Gets the stroke of the first row.  We allow backstroke starts, and derive this in the constructor
        """
        return self._start_stroke

    def early_calls(self) -> Dict[int, List[str]]:
        """See row_generator/row_generator.py for documentation."""
        return self._early_calls
