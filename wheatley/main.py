#!/usr/bin/env python3

"""
The file containing the main function for Wheatley, as well as all the command line argument parsing
required to make Wheatley easily configurable.
"""

import argparse
import logging
import os
import sys

from typing import List, Optional

from wheatley.rhythm import Rhythm, RegressionRhythm, WaitForUserRhythm
from wheatley.tower import RingingRoomTower
from wheatley.bot import Bot
from wheatley.page_parser import get_load_balancing_url, TowerNotFoundError, InvalidURLError
from wheatley.parsing import parse_peal_speed, PealSpeedParseError, parse_call

from wheatley.row_generation import RowGenerator, ComplibCompositionGenerator
from wheatley.row_generation import MethodPlaceNotationGenerator
from wheatley.row_generation.complib_composition_generator import PrivateCompError, InvalidCompError
from wheatley.row_generation.method_place_notation_generator import MethodNotFoundError, \
                                                                    generator_from_special_title
from wheatley.row_generation.place_holder_generator import PlaceHolderGenerator


def create_row_generator(args: argparse.Namespace) -> RowGenerator:
    """ Generates a row generator according to the given CLI arguments. """
    if "complib_share_link" in args and args.complib_share_link is not None:
        try:
            row_gen = ComplibCompositionGenerator.from_url(args.complib_share_link)
        except (PrivateCompError, InvalidCompError) as e:
            sys.exit(f"Bad value for '--comp': {e}")
    elif "comp" in args and args.comp is not None:
        try:
            row_gen = ComplibCompositionGenerator(args.comp)
        except (PrivateCompError, InvalidCompError) as e:
            sys.exit(f"Bad value for '--comp': {e}")
    elif "method" in args:
        try:
            row_gen = generator_from_special_title(args.method) or \
                      MethodPlaceNotationGenerator(
                          args.method,
                          parse_call(args.bob),
                          parse_call(args.single),
                          args.start_index
                      )
        except MethodNotFoundError as e:
            sys.exit(f"Bad value for '--method': {e}")
    else:
        assert False, \
            "This shouldn't be possible because one of --method and --comp should always be defined"

    return row_gen


def create_rhythm(peal_speed: int, inertia: float, max_bells_in_dataset: int, handstroke_gap: float,
                  use_wait: bool, initial_inertia: float=0) -> Rhythm:
    """ Generates a rhythm object according to the given CLI arguments. """
    # Sets the minimum number of bells that Wheatley will use in order to deduce a rhythm.  Setting this to
    # larger numbers will make Wheatley more stable during the pull-off, whereas smaller numbers will make
    # Wheatley more sensitive to user's pull-off speed.  If this is larger than `--max_bells_in_dataset`,
    # this will be clamped to fit.
    min_bells_in_dataset = 4

    # Clamp min_bells_in_dataset to not be bigger than max_bells_in_dataset
    min_bells_in_dataset = min(min_bells_in_dataset, max_bells_in_dataset)

    regression = RegressionRhythm(
        inertia,
        handstroke_gap=handstroke_gap,
        peal_speed=peal_speed,
        min_bells_in_dataset=min_bells_in_dataset,
        max_bells_in_dataset=max_bells_in_dataset,
        initial_inertia=initial_inertia
    )

    if use_wait:
        return WaitForUserRhythm(regression)

    return regression


def get_version_number() -> str:
    """
    Try to read the file with the version number, if not print an error and set a poison value as the
    version.
    """
    try:
        version_file_path = os.path.join(os.path.split(__file__)[0], "version.txt")

        with open(version_file_path) as f:
            return f.read()
    except IOError:
        return "<NO VERSION FILE FOUND>"


def configure_logging(verbose: bool, quietness: int) -> None:
    """ Sets up the logging for Wheatley. """
    logging.basicConfig(level=logging.WARNING)

    # Verboseness is a numerical represntation of the log level, with the following cases:
    # >= 1 -> DEBUG
    #    0 -> INFO
    #   -1 -> WARNING
    #   -2 -> ERROR
    # < -2 -> CRITICAL (Wheatley doesn't emit any CRITICAL logs, so this is essentially silent)
    verboseness: int = (1 if verbose else 0) - quietness

    if verboseness >= 1:
        log_level = logging.DEBUG
    elif verboseness == 0:
        log_level = logging.INFO
    elif verboseness == -1:
        log_level = logging.WARNING
    elif verboseness == -2:
        log_level = logging.ERROR
    else:  # verboseness <= -3
        log_level = logging.CRITICAL

    logging.getLogger(Bot.logger_name).setLevel(log_level)
    logging.getLogger(RingingRoomTower.logger_name).setLevel(log_level)
    logging.getLogger(RowGenerator.logger_name).setLevel(log_level)
    logging.getLogger(RegressionRhythm.logger_name).setLevel(log_level)
    logging.getLogger(WaitForUserRhythm.logger_name).setLevel(log_level)


def server_main(override_args: Optional[List[str]], stop_on_join_tower: bool) -> None:
    """
    The main function of Wheatley when spawned by the Ringing Room server.
    This has many many fewer options than the standard `main` function, on the basis that this running mode
    is designed to take its parameters over SocketIO whilst running, rather than from the CLI args.
    """
    __version__ = get_version_number()

    parser = argparse.ArgumentParser(
        description="A bot to fill in bells during ringingroom.com practices (server mode)."
    )

    parser.add_argument(
        "room_id",
        type=int,
        help="The numerical ID of the tower to join, represented as a row on 9 bells, \
              e.g. 763451928."
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        help="The port of the SocketIO server (which must be hosted on localhost)."
    )
    parser.add_argument(
        "-l", "--look-to-time",
        type=float,
        help="Set to the time when 'Look to' was called if Wheatley was spawned because 'look to' was \
              called and Wheatley is needed."
    )
    parser.add_argument(
        "-i", "--id",
        type=int,
        help="The instance ID of this Wheatley process."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Makes Wheatley print more (DEBUG) output."
    )
    parser.add_argument(
        "-q", "--quiet",
        action="count",
        default=0,
        help="Makes Wheatley print less output.  `-q` only prints WARNINGs and ERRORs; `-qq` only prints \
              ERRORs; `-qqq` prints nothing."
    )

    # Parse arguments
    # `[1:]` is apparently needed, because sys.argv[0] is the working file of the Python interpreter
    # which `parser.parse_args` does not want to see as an argument
    args = parser.parse_args(sys.argv[1:] if override_args is None else override_args)

    # Run the program
    configure_logging(args.verbose, args.quiet)

    # Log the version string to 'DEBUG'
    logging.debug(f"Running Wheatley {__version__}")

    # Args that we are currently 'missing'
    use_up_down_in = True
    stop_at_rounds = True
    peal_speed = 180
    inertia = 1
    initial_inertia = 0
    max_bells_in_dataset = 15
    handstroke_gap = 1
    use_wait = True
    call_comps = True

    tower_url = "http://127.0.0.1:" + str(args.port)

    tower = RingingRoomTower(args.room_id, tower_url)
    rhythm = create_rhythm(peal_speed, inertia, max_bells_in_dataset, handstroke_gap, use_wait,
                           initial_inertia)
    bot = Bot(tower, PlaceHolderGenerator(), use_up_down_in, stop_at_rounds, call_comps, rhythm,
              user_name="Wheatley", server_instance_id=args.id)

    with tower:
        tower.wait_loaded()

        if args.look_to_time is not None:
            bot.look_to_has_been_called(args.look_to_time)

        if not stop_on_join_tower:
            bot.main_loop()


def console_main(override_args: Optional[List[str]], stop_on_join_tower: bool) -> None:
    """
    The main function of Wheatley, when called from the Command Line.
    This parses the CLI arguments, creates the Rhythm, RowGenerator and Bot objects, then starts
    Wheatley's mainloop.

    The two optional arguments are used by the integration tester to give Wheatley artificial argument values
    (override_args) and make Wheatley exit with error code 0 on joining a tower so that hanging forever
    can be differentiated from Wheatley's normal behaviour of sitting in an infinite loop waiting for input.
    """
    __version__ = get_version_number()

    # PARSE THE ARGUMENTS

    parser = argparse.ArgumentParser(
        description="A bot to fill in bells during ringingroom.com practices"
    )

    # Tower arguments
    tower_group = parser.add_argument_group("Tower arguments")
    tower_group.add_argument(
        "room_id",
        type=int,
        help="The numerical ID of the tower to join, represented as a row on 9 bells, \
              e.g. 763451928."
    )
    tower_group.add_argument(
        "--url",
        default="https://ringingroom.com",
        type=str,
        help="The URL of the server to join (defaults to 'https://ringingroom.com')"
    )
    tower_group.add_argument(
        "--name",
        default=None,
        type=str,
        help="If set, then Wheatley will ring bells assigned to the given name. \
             When not set, Wheatley rings unassigned bells."
    )

    # Row generation arguments
    row_gen_group = parser.add_argument_group("Row generation arguments")

    # An mutual exclusion group to disallow specifying both a method *and* a CompLib comp
    comp_method_group = row_gen_group.add_mutually_exclusive_group(required=True)
    comp_method_group.add_argument(
        "-c", "--comp",
        type=int,
        help="The ID of the complib composition you want to ring"
    )
    comp_method_group.add_argument(
        "--complib-share-link",
        type=str,
        help="The link from the 'share' button of the private complib composition you want to ring.  For \
              example, \
              https://complib.org/composition/73905?accessKey=67622abc16397c0e7df32d5f98e3b206bef980c6."
    )
    comp_method_group.add_argument(
        "-m", "--method",
        type=str,
        help="The title of the method you want to ring"
    )

    row_gen_group.add_argument(
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
    row_gen_group.add_argument(
        "-n",
        "--single",
        default="1234",
        help='An override for what place notation(s) should be made when a `Single` is called in \
              Ringing Room.  These will by default happen at the lead end.  Examples: "1678" or \
              "0:1678" => 6ths place lead end single.  "-1:3.123" => a Grandsire Single. \
              "20: 7890" => a 7890 single taking effect 20 changes into a lead (the Half Lead for \
              Surprise Royal). "3: 567/9: 567" => singles in Stedman Triples.  Defaults to "1234".'
    )
    row_gen_group.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Determines which row of the lead Wheatley will start ringing.  This can be negative (so -1 \
              would refer to the lead **end**).  Defaults to 0 (i.e. a standard start)."
    )
    row_gen_group.add_argument(
        "-u", "--use-up-down-in",
        action="store_true",
        help="If set, then the Wheatley will automatically go into changes after two rounds have been \
              rung."
    )
    row_gen_group.add_argument(
        "-s", "--stop-at-rounds",
        action="store_true",
        help="If set, then Wheatley will stand his bells the first time rounds is reached."
    )
    row_gen_group.add_argument(
        "-H", "--handbell-style",
        action="store_true",
        help="If set, then Wheatley will ring 'handbell style', i.e. ringing two strokes of \
              rounds then straight into changes, and stopping at the first set of rounds. By \
              default, he will ring 'towerbell style', i.e. only taking instructions from the \
              ringing-room calls. This is equivalent to using the '-us' flags."
    )
    row_gen_group.add_argument(
        "--no-calls",
        action="store_true",
        help="If set, Wheatley will not call anything when ringing compositions."
    )

    # Rhythm arguments
    rhythm_group = parser.add_argument_group("Rhythm arguments")
    rhythm_group.add_argument(
        "-k", "--keep-going",
        action="store_true",
        help="If set, Wheatley will not wait for users to ring - instead, he will push on with the \
              rhythm."
    )
    rhythm_group.add_argument(
        "-w", "--wait",
        action="store_true",
        help="Legacy parameter, which is now set by default. The previous default behaviour of not waiting \
              can be set with '-k'/'--keep-going'."
    )
    rhythm_group.add_argument(
        "-I", "--inertia",
        type=float,
        default=0.5,
        help="Overrides Wheatley's 'inertia' - how much Wheatley will take other ringers' positions \
              into account when deciding when to ring.  0.0 means he will cling as closely as \
              possible to the current rhythm, 1.0 means that he will completely ignore the other \
              ringers."
    )
    rhythm_group.add_argument(
        "-S", "--peal-speed",
        default="2h58",
        help="Sets the default speed that Wheatley will ring (assuming a peal of 5040 changes), \
              though this will usually be adjusted by Wheatley whilst ringing to keep with other \
              ringers.  Example formatting: '3h4' = '3h4m' = '3h04m' = '3h04' = '184m' = '184'. \
              Defaults to '2h58'."
    )
    rhythm_group.add_argument(
        "-G", "--handstroke-gap",
        type=float,
        default=1.0,
        help="Sets the handstroke gap as a factor of the space between two bells.  Defaults to \
              '1.0'."
    )
    rhythm_group.add_argument(
        "-X", "--max-bells-in-dataset",
        type=int,
        default=15,
        help="Sets the maximum number of bells that Wheatley will store to determine the current \
              ringing speed.  If you make this larger, then he will be more consistent but less \
              quick to respond to changes in rhythm.  Setting both this and \
              --inertia to a very small values could result in Wheatley ringing ridiculously \
              quickly.  Defaults to '15'."
    )

    # Misc arguments
    parser.add_argument(
        "--version",
        action="version",
        version=f"Wheatley {__version__}"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Makes Wheatley print more (DEBUG) output."
    )
    parser.add_argument(
        "-q", "--quiet",
        action="count",
        default=0,
        help="Makes Wheatley print less output.  `-q` only prints WARNINGs and ERRORs; `-qq` only prints \
              ERRORs; `-qqq` prints nothing."
    )


    # Parse arguments
    # `[1:]` is apparently needed, because sys.argv[0] is the working file of the Python interpreter
    # which `parser.parse_args` does not want to see as an argument
    args = parser.parse_args(sys.argv[1:] if override_args is None else override_args)

    # Deprecation warnings
    if args.wait:
        print("Deprecation warning: `--wait` has been replaced with `--keep-going`!")

    # Run the program
    configure_logging(args.verbose, args.quiet)

    try:
        tower_url = get_load_balancing_url(args.room_id, args.url)
    except TowerNotFoundError as e:
        sys.exit(f"Bad value for 'room_id': {e}")
    except InvalidURLError as e:
        sys.exit(f"Bad value for '--url': {e}")

    tower = RingingRoomTower(args.room_id, tower_url)
    row_generator = create_row_generator(args)

    try:
        peal_speed = parse_peal_speed(args.peal_speed)
    except PealSpeedParseError as e:
        sys.exit(f"{e}")

    rhythm = create_rhythm(peal_speed, args.inertia, args.max_bells_in_dataset, args.handstroke_gap,
                           not args.keep_going)
    bot = Bot(tower, row_generator, args.use_up_down_in or args.handbell_style,
              args.stop_at_rounds or args.handbell_style, not args.no_calls, rhythm, user_name=args.name)

    # Catch keyboard interrupts and just print 'Bye!' instead a load of guff
    try:
        with tower:
            tower.wait_loaded()
            if not stop_on_join_tower:
                bot.main_loop()
    except KeyboardInterrupt:
        print("Bye!")

def main(override_args: Optional[List[str]]=None, stop_on_join_tower: bool=False) -> None:
    """
    The root main function for Wheatley.  If the first argument given to Wheatley is 'server-mode', then
    this will run `server_main` (the main function for running Wheatley on RR's servers) otherwise it will
    run `console_main` (the main function for running Wheatley from the Command Line).
    """
    # If the user adds 'server-mode' to the command, run the server-mode main function instead of this one,
    # and remove the 'server-mode' argument
    unparsed_args = override_args or sys.argv[1:]
    if len(unparsed_args) > 1 and unparsed_args[0] == "server-mode":
        del unparsed_args[0]
        server_main(unparsed_args, stop_on_join_tower)
        # The `server_main` function shouldn't return, but if it does somehow manage to do so return instead
        # of running the standard main function as well
    else:
        console_main(unparsed_args, stop_on_join_tower)



if __name__ == "__main__":
    main()
