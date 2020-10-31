""" Contains the RowGenerator subclass for generating rows from a CompLib composition. """

import json
from typing import Optional, List, Tuple

import requests

from wheatley.aliases import Row
from wheatley.stroke import Stroke
from wheatley.bell import Bell
from .row_generator import RowGenerator


class PrivateCompError(ValueError):
    """ An error class thrown when a user tries to access a private CompLib composition. """

    def __init__(self, comp_id: int) -> None:
        super().__init__()

        self._comp_id = comp_id

    def __str__(self) -> str:
        return f"Composition with ID {self._comp_id} is private."


class InvalidCompError(ValueError):
    """ An error class thrown when a user tries to access an invalid CompLib composition. """

    def __init__(self, comp_id: int) -> None:
        super().__init__()

        self._comp_id = comp_id

    def __str__(self) -> str:
        return f"Composition with ID {self._comp_id} is does not exist."


class InvalidComplibURLError(Exception):
    """ An error class thrown when a user inputs an invalid complib comp URL. """

    def __init__(self, url: str, error: str) -> None:
        super().__init__()

        self._url = url
        self._error = error

    def __str__(self) -> str:
        return f"Invalid CompLib URL {self._url}: {self._error}"


# The 'removeprefix' function from Python 3.9
def removeprefix(string: str, prefix: str) -> str:
    """ Removes a prefix from a given string if it exists. """
    if string.startswith(prefix):
        return string[len(prefix):]
    return string[:]


class ComplibCompositionGenerator(RowGenerator):
    """ The RowGenerator subclass for generating rows from a CompLib composition. """

    complib_url = "https://api.complib.org/composition/"

    def __init__(self, comp_id: int, access_key: Optional[str]=None) -> None:
        # Generate URL and request the rows
        url = self.complib_url + str(comp_id) + "/rows"
        if access_key:
            url += "?accessKey=" + access_key
        request_rows = requests.get(url)
        # Check for the status of the requests
        if request_rows.status_code == 404:
            raise InvalidCompError(comp_id)
        if request_rows.status_code == 403:
            raise PrivateCompError(comp_id)
        request_rows.raise_for_status()
        # Parse the request responses as JSON
        response_rows = json.loads(request_rows.text)
        unparsed_rows = response_rows['rows']
        # Determine the start row of the composition
        num_starting_rounds = 0
        while unparsed_rows[num_starting_rounds][0] == unparsed_rows[0][0]:
            num_starting_rounds += 1
        self._start_stroke = Stroke.from_index(num_starting_rounds)

        # Derive the rows, calls and stage from the JSON response
        self.loaded_rows: List[Tuple[Row, Optional[str]]] = [
            (
                Row([Bell.from_str(bell) for bell in row]),
                None if call == '' else call
            ) for row, call, property_bitmap in unparsed_rows[num_starting_rounds:]
        ]
        stage = response_rows['stage']

        # Variables from which the summary string is generated
        self.comp_id = comp_id
        self.comp_title = response_rows['title']
        self.is_comp_private = access_key is not None

        super().__init__(stage)

    @classmethod
    def from_url(cls, url: str) -> RowGenerator:
        """ Generates a ComplibCompositionGenerator from a URL to that composition. """
        # ==== CANONICALISATION ====
        # Always strip the 'https://' and 'www.' from the front of the URL
        canonical_url = url
        canonical_url = removeprefix(canonical_url, "https://")
        canonical_url = removeprefix(canonical_url, "www.")

        parts = canonical_url.split("?accessKey=")
        main_url = parts[0]
        try:
            access_key: Optional[str] = parts[1]
        except IndexError:
            access_key = None

        main_url_parts = main_url.split("/")

        try:
            if not main_url_parts[0].endswith("complib.org"):
                raise InvalidComplibURLError(url, "Doesn't point to 'complib.org'.")
            if main_url_parts[1] != "composition":
                raise InvalidComplibURLError(url, "Not a composition.")
            comp_id = int(main_url_parts[2])
        except KeyError as e:
            raise InvalidComplibURLError(url, "URL has too few segments.") from e
        except ValueError as e:
            raise InvalidComplibURLError(url, f"ID {main_url_parts[2]} is not an integer.") from e

        return cls(comp_id, access_key)

    def summary_string(self) -> str:
        """ Returns a short string summarising the RowGenerator. """
        return f"{'private ' if self.is_comp_private else ''}comp #{self.comp_id}: {self.comp_title}"

    def _gen_row(self, _previous_row: Row, _stroke: Stroke, index: int) -> Row:
        if index < len(self.loaded_rows):
            return self.loaded_rows[index][0]
        return self.rounds()

    def start_stroke(self) -> Stroke:
        """ Gets the stroke of the first row.  We allow backstroke starts, and derive this in the constructor
        """
        return self._start_stroke
