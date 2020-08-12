# Contributing
Pull requests are welcome, but please
[make an issue](https://github.com/Kneasle/ringing-room-bot/issues/new) to discuss the changes
before starting to implement things.

To run the bot **from source code**, `cd` to the repository directory and run:
```bash
python3 run-wheatley [ARGS]
```
(or `python run-wheatley [ARGS]` on Windows).

Or, on Unix you can run `./run-wheatley [ARGS]`.

## Code structure
```
.
├── CHANGE_LOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── requirements.txt
├── run-wheatley                                    => A shell-executable python script to launch Wheatley
├── setup.py                                        => Build script run to generate the PIP package
├── wheatley
│   ├── __init__.py                                 => Empty file
│   ├── __main__.py                                 => Code to start the bot
│   ├── arg_parsing.py                              => Code to parse formatted CLI args e.g. call strings
│   ├── bell.py                                     => Stores the representation of a bell
│   ├── bot.py                                      => The main class for the bot
│   ├── calls.py                                    => Constants for the calls used in Ringing Room
│   ├── main.py                                     => Entry point of the bot
│   ├── page_parser.py                              => Code to parse the ringing room HTML
│   ├── regression.py                               => Code for the weighted linear regression
│   ├── rhythm.py                                   => Code used to drive the bot's rhythm
│   ├── tower.py                                    => Code used to interact with ringing room
│   └── row_generation                              => Modular row generators
│       ├── __init__.py
│       ├── complib_composition_generator.py
│       ├── dixonoids_generator.py
│       ├── go_and_stop_calling_generator.py
│       ├── helpers.py
│       ├── method_place_notation_generator.py
│       ├── place_notation_generator.py
│       ├── plain_hunt_generator.py
│       └── row_generator.py
├── tests
│   ├── __init__.py
│   ├── test_arg_parsing.py                         => Unit tests for CLI arg parsing
│   └── row_generation                              => Unit tests for the row generation module
│       ├── __init__.py
│       ├── generator_test_helpers.py
│       ├── test_DixonoidsGenerator.py
│       ├── test_Helpers.py
│       ├── test_MethodPlaceNotationGenerator.py
│       ├── test_PlaceNotationGenerator.py
│       └── test_PlainHuntGenerator.py
├── fuzz                                            => Shell-executable script to run all the fuzzing
└── fuzzing
    ├── __init__.py
    ├── call_parsing.py
    └── fuzz_utils.py
 ```
