#!/usr/bin/env python3

"""
A shell-executable script to run all the commands contained in README.md or specified in EXTRA_TESTS and
assert that Wheatley does not crash.  With decent test coverage, this prevents mistakes like silly crashes
and argument errors.
"""

from subprocess import STDOUT, check_output, CalledProcessError, TimeoutExpired, Popen, PIPE
import subprocess
import time
import os
import shlex
import sys

# ID of a tower that I made called 'DO NOT ENTER'
ROOM_ID = "238915467"
EXAMPLE_METHOD = "Plain Bob Major"
IGNORE_STRING = "<!--- doctest-ignore -->"


# Tests that should be run on top of the examples from README.md
EXTRA_TESTS = []


def get_all_tests():
    """ Get all commands that should be tested (these should start with 'wheatley [ID NUMBER]'). """

    tests = []

    with open("README.md") as readme:
        is_in_code = False
        ignore_next_examples = False

        for i, l in enumerate(readme.read().split("\n")):
            stripped_line = l.strip()

            # If we see the line IGNORE_STRING, we should ignore the next block of examples
            if not is_in_code and stripped_line == IGNORE_STRING:
                ignore_next_examples = True

            if stripped_line.startswith("```"):
                # Alternate into or out of code blocks
                is_in_code = not is_in_code

                # Clear the ignore flag whenever we *finish* a code block
                if not is_in_code:
                    ignore_next_examples = False

            # If this is a code line that starts with `wheatley`, then it should be used as an example
            if is_in_code and stripped_line.startswith("wheatley"):
                if ignore_next_examples:
                    print(f"Ignoring README.md:{i}: {stripped_line}")
                else:
                    tests.append((f"README.md:{i}", stripped_line))

    return tests + [(f"EXTRA_TESTS:{i}", cmd) for i, cmd in EXTRA_TESTS]


def command_to_converted_args(location, command):
    # Bit of a hack, but this will convert commands starting with 'wheatley' to start with './run-wheatley'
    # and make sure that [ID NUMBER] is replaced with a valid room ID.  This way, the tests will run on the
    # version contained in the current commit, rather than a release version.
    edited_command = "python ./run-" + command.replace("[ID NUMBER]", ROOM_ID) \
                                       .replace("[METHOD TITLE]", '"' + EXAMPLE_METHOD + '"')
    insert_arg_index = 2

    # Check if running inside venv, if so we need to activate in each process
    if sys.prefix != sys.base_prefix and os.name == 'nt':
        # Windows path `\` gets dropped, but Windows is happy to accept `/` instead
        activate_script = sys.prefix.replace("\\", "/") + "/Scripts/activate"
        activate_script += ".bat"
        edited_command = activate_script + " & " + edited_command
        insert_arg_index = 4


    args = shlex.split(edited_command)
    args.insert(insert_arg_index, "integration-test")

    return (args, location, edited_command)



# I'm not sure how to do this in python.  I want `run_test` to return one of 3 types: an 'OK', a 'TIMEOUT'
# or an 'ERROR' with a return code and an output.  These two classes and None are trying to represent the
# enum:
#
# enum TestResult {
#     Ok,
#     Timeout,
#     Error(usize, String),
# }
class Timeout:
    def __init__(self):
        pass

    def result_text(self):
        return "TIMEOUT"


class CommandError:
    def __init__(self, return_code, output):
        self.return_code = return_code
        self.output = output

    def result_text(self):
        return "ERROR"


def run_test(args):
    try:
        check_output(args, stderr=STDOUT, timeout=5)
    except CalledProcessError as e:
        return CommandError(e.returncode, e.output.decode('utf-8'))
    except TimeoutExpired:
        return Timeout()

def check_test(proc):
    try:
        out, err = proc.communicate(timeout=5)
    except proc.returncode != 0:
        return CommandError(proc.returncode, err)
    except TimeoutExpired:
        proc.kill()
        return Timeout()

def main():
    """ Generate and run all the tests, asserting that Wheatley does not crash. """
    errors = []
    procs = []

    # Generate all the edited commands upfront, so that we can line up all the errors
    converted_commands = [command_to_converted_args(location, cmd) for (location, cmd) in get_all_tests()]

    max_command_length = max([len(cmd) for (_, _, cmd) in converted_commands])

    converted_commands_count = len(converted_commands)
    for i in range(converted_commands_count):
        print(converted_commands[i][0])
        (args, location, edited_command) = converted_commands[i]
        procs.append(Popen(args, stderr = STDOUT, stdout = subprocess.PIPE))

    print('Jobs started')

    for i in range(converted_commands_count):
        (args, location, edited_command) = converted_commands[i]
        error = check_test(procs[i])

        result_text = "ok"

        if error is not None:
            errors.append((location, edited_command, error))

            result_text = error.result_text()

        print(edited_command + " " + "." * (max_command_length + 3 - len(edited_command)) + " " + result_text)

    # Iterate over the errors
    if len(errors) == 0:
        print("ALL OK")
        return

    print("ERRORS FOUND:")
    for (location, command, e) in errors:
        print("\n")
        print(f" >>> {location}: {command}")

        if type(e) == CommandError:
            print(f"RETURN CODE: {e.return_code}")
            print(f"OUTPUT:\n{e.output}")
        if type(e) == Timeout:
            print("TIMED OUT")

    exit(1)


if __name__ == '__main__':
    main()
