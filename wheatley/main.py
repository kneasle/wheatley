#!/usr/bin/env python3

"""
The file containing the main function for the bot, as well as all the command line argument parsing
required to make the bot easily configurable.
"""

import argparse
import logging
import os
import sys

from wheatley.rhythm import RegressionRhythm, WaitForUserRhythm
from wheatley.tower import RingingRoomTower
from wheatley.bot import Bot
from wheatley.page_parser import get_load_balancing_url
from wheatley.row_generation import RowGenerator, ComplibCompositionGenerator
from wheatley.row_generation import MethodPlaceNotationGenerator


def row_generator(args):
    """ Generates a row generator according to the given CLI arguments. """

    if "comp" in args and args.comp is not None:
        row_gen = ComplibCompositionGenerator(args.comp)
    elif "method" in args:
        row_gen = MethodPlaceNotationGenerator(args.method)
    else:
        assert False, \
            "This shouldn't be possible because one of --method and --comp should always be defined"

    # row_gen = PlainHuntGenerator(8)
    # row_gen = PlaceNotationGenerator(8, "x1", bob={1: "6"})
    # row_gen = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
    # row_gen = PlaceNotationGenerator.stedman(11)

    return row_gen


class PealSpeedParseError(ValueError):
    """
    An error thrown with a helpful error message when the user inputs a peal speed string that
    cannot be parsed by the parser.
    """

    def __init__(self, peal_spead_string, message):
        super().__init__()

        self.peal_spead_string = peal_spead_string
        self.message = message

    def __str__(self):
        return f"Error parsing peal speed '{self.peal_spead_string}': {self.message}"


def parse_peal_speed(peal_speed: str):
    """
    Parses a peal speed written in the format /2h58(m?)/ or /XXX(m?)/ into a number of minutes.
    """

    def exit_with_message(error_text):
        """ Raise an exception with a useful error message. """

        raise PealSpeedParseError(peal_speed, error_text)

    # Strip whitspace from the argument, so that if the user is in fact insane enough to pad their
    # CLI arguments with whitespace then they can do so and not crash the program.  This also has
    # the side effect of cloning the input string so we can freely modify it.
    stripped_peal_speed = peal_speed.strip()

    # Remove the 'm' from the end of the peal speed - it doesn't add any clarity
    if stripped_peal_speed.endswith("m"):
        stripped_peal_speed = stripped_peal_speed[:-1]

    if "h" in stripped_peal_speed:
        # Split the peal speed into its hour and minute components, and print a helpful message
        # if there are too many parts
        split_parts = stripped_peal_speed.split("h")

        if len(split_parts) > 2:
            exit_with_message("The peal speed should contain at most one 'h'.")

        hour_string, minute_string = split_parts

        # Strip the input values so that the user can put whitespace into the input if they want
        hour_string = hour_string.strip()
        minute_string = minute_string.strip()

        # Parse the hours value, and print messages if it is invalid
        try:
            hours = int(hour_string)
        except ValueError:
            exit_with_message(f"The hour value '{hour_string}' is not an integer.")

        if hours < 0:
            exit_with_message(f"The hour value '{hour_string}' must be a positive integer.")

        # Parse the minute value, and print messages if it is invalid
        try:
            minutes = 0 if minute_string == "" else int(minute_string)
        except ValueError:
            exit_with_message(f"The minute value '{minute_string}' is not an integer.")

        if minutes < 0:
            exit_with_message(f"The minute value '{minute_string}' must be a positive integer.")

        if minutes > 59:
            exit_with_message(f"The minute value '{minute_string}' must be smaller than 60.")

        return hours * 60 + minutes

    # If the user doesn't put an 'h' in their string, then we assume it's just a minute value that
    # may or may not be bigger than 60
    try:
        minutes = int(stripped_peal_speed)
    except ValueError:
        exit_with_message(f"The minute value '{stripped_peal_speed}' is not an integer.")

    if minutes < 0:
        exit_with_message(f"The minute value '{stripped_peal_speed}' must be a positive integer.")

    return minutes


def rhythm(args):
    """ Generates a rhythm object according to the given CLI arguments. """

    try:
        peal_speed = parse_peal_speed(args.peal_speed)
    except PealSpeedParseError as e:
        sys.exit(str(e))

    regression = RegressionRhythm(
        args.inertia,
        handstroke_gap=args.handstroke_gap,
        peal_speed=peal_speed,
        max_rows_in_dataset=args.max_rows_in_dataset
    )

    if args.wait:
        return WaitForUserRhythm(regression)

    return regression


def configure_logging():
    """ Sets up the logging for the bot. """

    logging.basicConfig(level=logging.WARNING)

    logging.getLogger(RingingRoomTower.logger_name).setLevel(logging.INFO)
    logging.getLogger(RowGenerator.logger_name).setLevel(logging.INFO)
    logging.getLogger(RegressionRhythm.logger_name).setLevel(logging.INFO)
    logging.getLogger(WaitForUserRhythm.logger_name).setLevel(logging.INFO)


def main():
    """
    The main function of the bot.
    This parses the CLI arguments, creates the Rhythm, RowGenerator and Bot objects, then starts
    the bot's mainloop.
    """

    # Try to read the file with the version number, if not print an error and set a poison value
    # as the version
    try:
        version_file_path = os.path.join(os.path.split(__file__)[0], "version.txt")

        with open(version_file_path) as f:
            __version__ = f.read()
    except IOError:
        __version__ = "<NO VERSION FILE FOUND>"

    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="A bot to fill in bells during ringingroom.com practices"
    )

    parser.add_argument(
        "room_id",
        type=int,
        help="The numerical ID of the tower to join, represented as a row on 9 bells, \
              e.g. 763451928."
    )
    parser.add_argument(
        "--url",
        default="https://ringingroom.com",
        type=str,
        help="The URL of the server to join (defaults to 'https://ringingroom.com')"
    )
    parser.add_argument(
        "-u", "--use-up-down-in",
        action="store_true",
        help="If set, then the bot will automatically go into changes after two rounds have been \
              rung."
    )
    parser.add_argument(
        "-s", "--stop-at-rounds",
        action="store_true",
        help="If set, then the bot will stand its bells after rounds is reached."
    )
    parser.add_argument(
        "-H", "--handbell-style",
        action="store_true",
        help="If set, then the bot will ring 'handbell style', i.e. ringing two strokes of \
              rounds then straight into changes, and stopping at the first set of rounds. By \
              default, it will ring 'towerbell style', i.e. only taking instructions from the \
              ringing-room calls. This is equivalent to using the '-us' flags."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Wheatley v{__version__}"
    )

    # Rhythm arguments
    parser.add_argument(
        "-w", "--wait",
        action="store_true",
        help="If set, the bot will wait for users to ring rather than pushing on with the rhythm."
    )
    parser.add_argument(
        "-I", "--inertia",
        type=float,
        default=0.5,
        help="Overrides the bot's 'inertia' - now much the bot will take other ringers' positions \
              into account when deciding when to ring.  0.0 means it will cling as closely as \
              possible to the current rhythm, 1.0 means that it will completely ignore the other \
              ringers. By default, it will set a value depending on what proportion of the bells \
              are user controlled."
    )
    parser.add_argument(
        "-S", "--peal-speed",
        default="2h58",
        help="Sets the default speed that the bot will ring (assuming a peal of 5040 changes), \
              though this will usually be adjusted by the bot whilst ringing to keep with other \
              ringers.  Example formatting: '3h4' = '3h4m' = '3h04m' = '3h04' = '184m' = '184'. \
              Defaults to '2h58'."
    )
    parser.add_argument(
        "-G", "--handstroke-gap",
        type=float,
        default=1.0,
        help="Sets the handstroke gap as a factor of the space between two bells.  Defaults to \
              '1.0'."
    )
    parser.add_argument(
        "-X", "--max-rows-in-dataset",
        type=float,
        default=3.0,
        help="Sets the maximum number of rows that Wheatley will store to determine the current \
              ringing speed.  If you make this larger, then will be more consistent but less \
              quick to respond to changes in rhythm.  Defaults to '3.0'.  Setting both this and \
              --inertia to a very small values could result in Wheatley ringing ridiculously \
              quickly."
    )

    # Row generator arguments
    row_gen_group = parser.add_mutually_exclusive_group(required=True)
    row_gen_group.add_argument(
        "--comp",
        type=int,
        help="The ID of the complib composition you want to ring"
    )
    row_gen_group.add_argument(
        "--method",
        type=str,
        help="The title of the method you want to ring"
    )

    args = parser.parse_args()

    # Run the program
    configure_logging()

    tower = RingingRoomTower(args.room_id, get_load_balancing_url(args.room_id, args.url))
    bot = Bot(tower, row_generator(args), args.use_up_down_in or args.handbell_style,
              args.stop_at_rounds or args.handbell_style, rhythm=rhythm(args))

    with tower:
        tower.wait_loaded()

        print("=== LOADED ===")

        bot.main_loop()


if __name__ == "__main__":
    main()
