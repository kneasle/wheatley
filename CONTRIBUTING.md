# Contributing
Pull requests are welcome, but please
[make an issue](https://github.com/Kneasle/ringing-room-bot/issues/new) to discuss the changes
before starting to implement things.

To run the bot from source code, `cd` to the repository directory and run:
```bash
python3 rr_bot [ARGS]
```
(or `python rr_bot [ARGS]` on Windows).

## Code structure
```
.
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── requirements.txt
├── setup.py                                        => Build script run to generate the PIP package
├── rr_bot
│   ├── __init__.py                                 => Empty file
│   ├── __main__.py                                 => Code to start the bot
│   ├── bell.py                                     => Stores the representation of a bell
│   ├── bot.py                                      => The main class for the bot
│   ├── calls.py                                    => Constants for the calls used in Ringing Room
│   ├── main.py                                     => Entry point of the bot
│   ├── page_parser.py                              => Code to parse the ringing room HTML
│   ├── regression.py                               => Code for the weighted linear regression
│   ├── rhythm.py                                   => Code used to drive the bot's rhythm
│   ├── tower.py                                    => Code used to interact with ringing room
│   └── row_generation                              => Modular row generators
│       ├── __init__.py
│       ├── complib_composition_generator.py
│       ├── dixonoids_generator.py
│       ├── go_and_stop_calling_generator.py
│       ├── helpers.py
│       ├── method_place_notation_generator.py
│       ├── place_notation_generator.py
│       ├── plain_hunt_generator.py
│       └── row_generator.py
└── tests                                           => Unit tests for the row generation module
    ├── __init__.py
    └── row_generation
        ├── __init__.py
        ├── generator_test_helpers.py
        ├── test_DixonoidsGenerator.py
        ├── test_Helpers.py
        ├── test_MethodPlaceNotationGenerator.py
        ├── test_PlaceNotationGenerator.py
        └── test_PlainHuntGenerator.py
```
