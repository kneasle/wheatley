""" A module to hold common type aliases """

from typing import Any, Dict, NewType, List
from wheatley.bell import Bell


CallDef = NewType('CallDef', Dict[int, str])
JSON = Dict[str, Any]
Places = NewType('Places', List[int])
Row = NewType('Row', List[Bell])
