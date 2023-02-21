#!/usr/bin/env python3
import argparse
import os

import mypy.api
import pytest
from io import StringIO
from pylint.lint import Run as run_pylint
from pylint.reporters.text import TextReporter
import sys

import doctests
import fuzzing

parser = argparse.ArgumentParser(
    description="Run all or some checks on the codebase. Stops at first failed check"
)

parser.add_argument("--unit-tests", "-u", action="store_true", help="Run pytest on tests/")

parser.add_argument("--doc-tests", "-d", action="store_true", help="Run tests from examples in Readme.md")

parser.add_argument("--fuzz", "-f", action="store_true", help="Run fuzzing on parsing logic")

parser.add_argument("--lint", "-l", action="store_true", help="Run pylint on wheatley/ folder")

parser.add_argument("--type-check", "-t", action="store_true", help="Run mypy type check on wheatley/ folder")


class Check:
    def __init__(self, title: str):
        self.title = title

    def __enter__(self):
        width = 30
        stars = "*" * width
        padding = " " * ((width - len(self.title)) // 2)
        print(
            f"""
    *{stars}*
    *{padding}{self.title}{padding}*
    *{stars}*
        """
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            message = f"\u2705 {self.title} passed"
        else:
            message = f"\u274c {self.title} failed"
        try:
            print(message)
        except UnicodeEncodeError:
            print(message[2:])


# Ignore first argument (this file name)
mypy_args = sys.argv[1:]
parsed_args = parser.parse_args(mypy_args)
# Run all if no option specified
run_all = len(mypy_args) == 0

if run_all or parsed_args.unit_tests:
    with Check("Unit tests"):
        print("python -m pytest")
        exit_code = pytest.main([])
        if exit_code:
            exit(exit_code)

if run_all or parsed_args.doc_tests:
    with Check("Documentation tests"):
        print("python doctests.py")
        doctests.main()

if run_all or parsed_args.fuzz:
    with Check("Fuzzing"):
        print("python -m fuzzing")
        fuzzing.run()

if run_all or parsed_args.lint:
    with Check("Linting"):
        print("python -m pylint wheatley")
        pylint_args = ["wheatley"]
        if os.name != "nt":
            pylint_args.append("--enable=unexpected-line-ending-format")

        # Custom open stream
        pylint_output = StringIO()
        reporter = TextReporter(pylint_output)

        run_pylint(pylint_args, reporter=reporter, exit=False)

        output = pylint_output.getvalue()
        print(output)
        success = output.find("Your code has been rated at 10")
        if success == -1:
            exit(1)

if run_all or parsed_args.type_check:
    with Check("Type check"):
        print("python -m mypy wheatley --pretty --disallow-incomplete-defs --disallow-untyped-defs")
        mypy_args = ["wheatley", "--pretty", "--disallow-incomplete-defs", "--disallow-untyped-defs"]
        stdout, stderr, exit_status = mypy.api.run(mypy_args)
        print(stdout)
        print(stderr, file=sys.stderr)
        if exit_status:
            exit(exit_status)


print(
    """
====== Success ======
    """
)
