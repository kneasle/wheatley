from .call_parsing import fuzz_parse_call
from .peal_speed_parsing import fuzz_parse_peal_speed


def run():
    """ Run all the fuzzing tests """
    fuzz_parse_call()
    fuzz_parse_peal_speed()
