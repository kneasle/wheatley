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
from wheatley.page_parser import *
from wheatley.row_generation import RowGenerator, ComplibCompositionGenerator
from wheatley.row_generation import MethodPlaceNotationGenerator
from wheatley.arg_parsing import parse_peal_speed, PealSpeedParseError, parse_call


def row_generator(args):
    """ Generates a row generator according to the given CLI arguments. """

    if "comp" in args and args.comp is not None:
        row_gen = ComplibCompositionGenerator(args.comp)
    elif "method" in args:
        row_gen = MethodPlaceNotationGenerator(
            args.method,
            parse_call(args.bob),
            parse_call(args.single)
        )
    else:
        assert False, \
            "This shouldn't be possible because one of --method and --comp should always be defined"

    # row_gen = PlainHuntGenerator(8)
    # row_gen = PlaceNotationGenerator(8, "x1", bob={1: "6"})
    # row_gen = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
    # row_gen = PlaceNotationGenerator.stedman(11)

    return row_gen


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

    parser.add_argument(
        "-b",
        "--bob",
        default="14",
        help='An override for what place notation(s) should be made when a `Bob` is called in \
              Ringing Room.  These will by default happen at the lead end.  Examples: "16" or \
              "0:16" => 6ths place lead end bob.  "-1:3" or "-1:3.1" => a Grandsire Bob.  "20: 70" \
              => a 70 bob taking effect 20 changes into a lead (the Half Lead for Surprise Royal). \
              "20:7/0:4" => a 70 bob 20 changes into a lead and a 14 bob at the lead end. \
              "3: 5/9: 5" => bobs in Stedman Triples.  Defaults to "14".'
    )
    parser.add_argument(
        "-n",
        "--single",
        default="1234",
        help='An override for what place notation(s) should be made when a `Single` is called in \
              Ringing Room.  These will by default happen at the lead end.  Examples: "1678" or \
              "0:1678" => 6ths place lead end single.  "-1:3.123" => a Grandsire Single. \
              "20: 7890" => a 7890 single taking effect 20 changes into a lead (the Half Lead for \
              Surprise Royal). "3: 567/9: 567" => singles in Stedman Triples.  Defaults to "1234".'
    )

    args = parser.parse_args()

    # Run the program
    configure_logging()

    http_server_url = fix_url(args.url)

    try:
        socket_url = get_load_balancing_url(args.room_id, http_server_url)
    except (TowerNotFoundError, InvalidURLError) as e:
        sys.exit(f"Invalid argument: {e}")

    tower = RingingRoomTower(args.room_id, socket_url)
    bot = Bot(tower, row_generator(args), args.use_up_down_in or args.handbell_style,
              args.stop_at_rounds or args.handbell_style, rhythm=rhythm(args))

    with tower:
        tower.wait_loaded()

        print("=== LOADED ===")

        bot.main_loop()


if __name__ == "__main__":
    main()
