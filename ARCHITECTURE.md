# Architecture

This file provides a high-level overview of the code, inspired by
[matklad's blog post](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html) of the same name.
The purpose of this file is to provide a convenient 'mental map' of Wheatley's code to help new
contributors familiarise themselves with the code base.  It aims to answers general questions like
"where do I find code to do X?" or "what does the code in Y do?", but doesn't go into great detail
about the inner workings of each section.

## Bird's Eye View of the Problem

Wheatley is a 'bot' ringer for the Ringing Room platform.  Wheatley also adapts to the actions of
other human ringers _in real time_ rather than simply expecting them to keep up with a set pace.
To achieve this goal, Wheatley has three tasks once the start-up is complete:

1. Know what is being rung (i.e. what order are the bells expected to ring).  This can be affected
   dynamically by human ringers making calls like `Bob`, `Single`, `Go`, etc.
2. Listen for human-controlled bells being rung, and use this new information to update some
   internal sense of 'rhythm'.
3. Combine, in real time, the expected order of the bells (from 1.) with the real-time data from
   human ringers (from 2.) in order to ring the Wheatley-controlled bells at the 'right' times.

## Code Map

The bulk of the code resides in the `wheatley/` directory (which the only code is shipped to users).
However, there are some other pieces of code useful during development which reside in the main
directory:

- `run-wheatley`: An executable Python script which will run the Wheatley code directly as though it
  were run through `pip`.
- `tests/*`: Unit tests for various pieces of Wheatley's code.  This only tests code in the
  `wheatley/` folder.
- `doctests`: Python script which invokes all the examples found in `README.md`, asserting that they
  don't crash.  This prevents the examples from getting out of sync with the code.
- `fuzz`, `fuzzing/*`: Fuzzing for CLI argument parsers.  These feed the parsing fuctions with
  thousands of randomly generated inputs, asserting that they must produce well-defined errors.

### `wheatley/{aliases.py, bell.py, calls.py, stroke.py}`

These files contain little or no business logic, and instead provide datatypes (`bell.py`,
`stroke.py`), type aliases (`aliases.py`) and/or constants that are used extensively throughout the
code.  These serve two purposes: 
1. They increase safety by providing an abstraction layer over the raw numbers and strings used to
   communicate with Ringing Room.
2. `bell.py` prevents any ambiguity between the many different representations of bell names (i.e.
   is the 12th called `'T'` (name), `12` (number) or `11` (index)?) - Wheatley uses one `Bell` class
   which provides unambiguous conversions to and from these representations.

### `wheatley/bot.py`

This is the glue code that holds Wheatley together.  The `Bot` class is a singleton that gets
created at start-up and mediates interactions between other parts of the code (row generation,
rhythm, interacting with Ringing Room, etc).  It also runs the `mainloop` - an infinite loop in
which the main thread gets stuck until Wheatley stops.

**Architectural Invariant**: None of the code in `row_generation/*`, `rhythm/*` or `tower.py` can
talk directly to each other; instead they all provide an interface that the `Bot` class to mediate
interactions.

### `wheatley/rhythm/*`

This is where the rhythm detection happens.  The specification of a rhythm is defined in
`abstract_rhythm.py`, and there are two `Rhythm` classes which implement different behaviours:
- `regression.py` uses regression to draw a linear line of best fit through the user's datapoints
  and then uses this line to decide where Wheatley's bell should ring.
- `wait_for_user.py` adds waiting for user-controlled bells on top of an existing `Rhythm` class.

**Architectural Invariant**: The rhythm module should never access the real time directly - it
should use the times passed to each individual method.  This is because `WaitForUserRhythm` lies to
its internal rhythm in order to stop Wheatley from jumping back to the original rhythm if someone
holds up for a long time.

### `wheatley/row_generation/*`

This is the code that determines _what_ Wheatley rings, and reacts to the calls `Bob` and `Single`.
`row_generator.py` specifies the interface of a `RowGenerator`, and each different source of rows
(method, CompLib, dixonoid, etc.) has its own file and class.

**Architectural Invariant**: The `row_generation` module does _not_ handle adding cover bells or
responding to calls like `Go`, `That's All`, `Stand`.  These are both handled by the `Bot` class,
since both cover bells and state transitions are indepedent of what row generator is being used.

### `wheatley/{main.py, parsing.py}`

This is the start-up code for Wheatley.  It gets called once and is tasked with parsing the user's
input and then using this to generate `Rhythm`, `RowGenerator`, `Tower` and `Bot` singletons.
Finally, it enters the `Bot`'s mainloop, which never returns.

`parsing.py` also contains some code for interpreting the SocketIO signals which change the controls
in the integrated version, but this will likely be moved somewhere else.

Wheatley has 3 main functions:
- `server_main`: The integrated Ringing Room version's main function
- `console_main`: The CLI version's main function
- `main`:  The root main function, which delegates to one of the other two main functions depending
  on whether or not Wheatley is running on a Ringing Room server

**Architectural Invariant**:  This is the only place where different code is executed between the
CLI and integrated versions.  90% of the differences between versions are implemented by
disconnecting callbacks during initialisation.

### `wheatley/{tower.py, page_parsing.py}`

**NOTE: This code is soon going to be replaced with
[belltower](https://github.com/kneasle/belltower), which can be used for other projects.**

These files handle all the direct contact with Ringing Room, and provide an abstraction barrier
between the rest of the code and the internal workings of Ringing Room.  The `Tower` class in
`tower.py` handles run-time connections to Ringing Room, whereas `page_parsing.py` is used during
start-up to parse information out of the HTML source of the Ringing Room pages.

This abstraction layer means two things:
1. 90% of Wheatley is completely platform indepedent - supporting a new platform (other than Ringing
   Room) would only require creating a new `Tower` class.
2. If Ringing Room changes its API in any way, the corresponding changes to Wheatley are limited to
   just these files.

**Architectural Invariant**: Every interaction with Ringing Room is handled through these modules -
the rest of the code does't even know it's talking to Ringing Room.
