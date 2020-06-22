#!/usr/bin/env python3

"""
The file containing the main function for the bot, as well as all the command line argument parsing
required to make the bot easily configurable.
"""

import logging
import argparse

from rhythm import RegressionRhythm, WaitForUserRhythm
from tower import RingingRoomTower
from bot import Bot

from RowGeneration.ComplibCompositionReader import ComplibCompositionReader
# from RowGeneration.GoAndStopCallingGenerator import GoAndStopCallingGenerator
# from RowGeneration.DixonoidsGenerator import DixonoidsGenerator
from RowGeneration.MethodPlaceNotationGenerator import MethodPlaceNotationGenerator
# from RowGeneration.PlainHuntGenerator import PlainHuntGenerator
# from RowGeneration.PlaceNotationGenerator import PlaceNotationGenerator
from RowGeneration.RowGenerator import RowGenerator


def row_generator(args):
    """ Generates a row generator according to the given CLI arguments. """

    if "comp" in args and args.comp is not None:
        row_gen = ComplibCompositionReader(args.comp)
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


def rhythm(args):
    """ Generates a rhythm object according to the given CLI arguments. """

    regression = RegressionRhythm()

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

    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="A bot to fill in bells during ringingroom.com practices"
    )

    parser.add_argument(
        "--id",
        default=763451928,
        type=int,
        help="The ID of the tower to join (defaults to the ID of 'Bot Training Ground', 763451928)."
    )
    parser.add_argument(
        "--url",
        default="https://ringingroom.com",
        type=str,
        help="The URL of the server to join (defaults to 'https://ringingroom.com')"
    )
    parser.add_argument(
        "-w", "--wait",
        action="store_true",
        help="If set, the bot will wait for users to ring rather than pushing on with the rhythm."
    )

    # Row generator arguments
    row_gen_group = parser.add_mutually_exclusive_group()
    row_gen_group.add_argument(
        "--comp",
        type=int,
        help="The ID of the complib composition you want to ring"
    )
    row_gen_group.add_argument(
        "--method",
        default="Plain Bob Minor",
        type=str,
        help="The title of the method you want to ring"
    )

    args = parser.parse_args()

    # Run the program
    configure_logging()

    tower = RingingRoomTower(args.id, args.url)
    bot = Bot(tower, row_generator(args), rhythm=rhythm(args))

    with tower:
        tower.wait_loaded()

        print("=== LOADED ===")

        bot.main_loop()


if __name__ == "__main__":
    main()
