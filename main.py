#!/usr/bin/env python3

import logging
import time

from rhythm import RegressionRhythm, WaitForUserRhythm
from tower import RingingRoomTower
from bot import Bot

from RowGeneration.ComplibCompositionReader import ComplibCompositionReader
# from RowGeneration.GoAndStopCallingGenerator import GoAndStopCallingGenerator
from RowGeneration.DixonoidsGenerator import DixonoidsGenerator
from RowGeneration.MethodPlaceNotationGenerator import MethodPlaceNotationGenerator
from RowGeneration.PlainHuntGenerator import PlainHuntGenerator
from RowGeneration.PlaceNotationGenerator import PlaceNotationGenerator
from RowGeneration.RowGenerator import RowGenerator


def row_generator():
    row_gen = PlainHuntGenerator(8)
    # row_gen = PlaceNotationGenerator(8, "x1", bob={1: "6"})
    # row_gen = ComplibCompositionReader(65034)
    # row_gen = MethodPlaceNotationGenerator("Single Oxford Bob Triples")
    # row_gen = DixonoidsGenerator(6, DixonoidsGenerator.DixonsRules)
    row_gen = PlaceNotationGenerator.stedman(11)
    return row_gen


def rhythm():
    regression = RegressionRhythm()
    wait = WaitForUserRhythm(regression)
    return regression
    # return wait


def configure_logging():
    logging.basicConfig(level=logging.WARNING)

    logging.getLogger(RingingRoomTower.logger_name).setLevel(logging.INFO)
    logging.getLogger(RowGenerator.logger_name).setLevel(logging.INFO)
    logging.getLogger(RegressionRhythm.logger_name).setLevel(logging.INFO)
    logging.getLogger(WaitForUserRhythm.logger_name).setLevel(logging.INFO)


def main():
    configure_logging()

    tower = RingingRoomTower(763451928, "https://ringingroom.com")
    bot = Bot(tower, row_generator(), rhythm=rhythm())

    with tower:
        tower.wait_loaded()

        print("=== LOADED ===")

        bot.main_loop()


if __name__ == "__main__":
    main()
