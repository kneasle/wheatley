""" A module to hold common type aliases """

from typing import Any, Dict, List
from wheatley.bell import Bell

Call = Dict[int, str]
Row = List[Bell]
Places = List[int]
JSON = Dict[str, Any]
