""" Run a fuzzer to generate lots of random input for the call parser. """

from random import choice, randint

from wheatley.parsing import parse_call, CallParseError

from .fuzz_utils import fuzz_for_unwrapped_errors

def random_call_string():
    """ Generate a plausable input value for `wheatley.arg_parsing.parse_call` to parse. """

    return "".join([choice("1234567890ET:/.&#xx#?s ") for _ in range(randint(0, 20))])

fuzz_for_unwrapped_errors("parse_call", parse_call, random_call_string, CallParseError)
