""" Contains the RowGenerator subclass for generating rows from a CompLib composition. """

from typing import List, Optional

import requests

from wheatley.bell import Bell
from .row_generator import RowGenerator


class PrivateCompError(ValueError):
    """ An error class thrown when a user tries to access a private CompLib composition. """

    def __init__(self, comp_id):
        super().__init__()

        self._comp_id = comp_id

    def __str__(self):
        return f"Composition with ID {self._comp_id} is private."


class InvalidCompError(ValueError):
    """ An error class thrown when a user tries to access an invalid CompLib composition. """

    def __init__(self, comp_id):
        super().__init__()

        self._comp_id = comp_id

    def __str__(self):
        return f"Composition with ID {self._comp_id} is does not exist."


class InvalidComplibURLError(Exception):
    """ An error class thrown when a user inputs an invalid complib comp URL. """

    def __init__(self, url, error):
        super().__init__()

        self._url = url
        self._error = error

    def __str__(self):
        return f"Invalid CompLib URL {self._url}: {self._error}"


# The 'removeprefix' function from Python 3.9
def removeprefix(string, prefix: str) -> str:
    """ Removes a prefix from a given string if it exists. """
    if string.startswith(prefix):
        return string[len(prefix):]
    return string[:]


class ComplibCompositionGenerator(RowGenerator):
    """ The RowGenerator subclass for generating rows from a CompLib composition. """

    complib_url = "https://complib.org/composition/"

    def __init__(self, comp_id: int, access_key: Optional[str]=None):
        url = self.complib_url + str(comp_id) + "/rows"
        if access_key:
            url += "?accessKey=" + access_key
        request_rows = requests.get(url)

        if request_rows.status_code == 404:
            raise InvalidCompError(comp_id)

        if request_rows.status_code == 403:
            raise PrivateCompError(comp_id)

        request_rows.raise_for_status()

        # New line separated, skip the first line (rounds)
        split_rows = request_rows.text.splitlines(False)[1::]
        self.loaded_rows = [[Bell.from_str(bell) for bell in row] for row in split_rows]

        stage = len(self.loaded_rows[0])

        super().__init__(stage)

    @classmethod
    def from_url(cls, url):
        """ Generates a ComplibCompositionGenerator from a URL to that composition. """
        # ==== CANONICALISATION ====
        # Always strip the 'https://' and 'www.' from the front of the URL
        canonical_url = url
        canonical_url = removeprefix(canonical_url, "https://")
        canonical_url = removeprefix(canonical_url, "www.")

        parts = canonical_url.split("?accessKey=")
        main_url = parts[0]
        try:
            access_key = parts[1]
        except IndexError:
            access_key = None

        main_url_parts = main_url.split("/")

        try:
            if main_url_parts[0] != "complib.org":
                raise InvalidComplibURLError(url, "Doesn't point to 'complib.org'.")
            if main_url_parts[1] != "composition":
                raise InvalidComplibURLError(url, "Not a composition.")
            comp_id = int(main_url_parts[2])
        except KeyError as e:
            raise InvalidComplibURLError(url, "URL has too few segments.") from e
        except ValueError as e:
            raise InvalidComplibURLError(url, f"ID {main_url_parts[2]} is not an integer.") from e

        return cls(comp_id, access_key)

    def _gen_row(self, previous_row: List[Bell], is_handstroke: bool, index: int) -> List[Bell]:
        if index < len(self.loaded_rows):
            return self.loaded_rows[index]

        return self.rounds()
