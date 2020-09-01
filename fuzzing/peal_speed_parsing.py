""" Run a fuzzer to generate lots of random input for the peal speed parser. """

from random import choice, randint

from wheatley.parsing import parse_peal_speed, PealSpeedParseError

from .fuzz_utils import fuzz_for_unwrapped_errors

def random_peal_speed_string():
    """ Generate a plausable input value for `wheatley.arg_parsing.parse_peal_speed` to parse. """

    return "".join([choice("1234567890hm,\nx?ET ") for _ in range(randint(0, 20))])

fuzz_for_unwrapped_errors(
    "parse_peal_speed",
    parse_peal_speed,
    random_peal_speed_string,
    PealSpeedParseError
)
