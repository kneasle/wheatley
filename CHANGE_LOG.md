# 0.7.0 (W.I.P.)

## User-facing changes

- (#181) Make the behaviour of `That's All` more intuitive (i.e. calling `That's All` during rounds
  will no longer cause Wheatley to ring one erroneous row of method).
- (#159, thanks @chrisjfield) Start ringing at a custom row (using `--start-row <row>`).  This
  doesn't work for CompLib compositions.
- (#169, thanks @aajshaw) Ring arbitrary place notation on a given stage (using
  `--place-notation <stage>:<place-notation>`).  `--bob` and `--single` still apply.
- (#184) `--stop-at-rounds` now leaves the bells set at hand even if the touch finishes on a
  handstroke.
- (#179) Overhaul the `README.md`
- (#182) Ignore the `username` param when users leave (this is deprecated and will be removed in
  later versions of RR)

## Internal Improvements

- (#197) Use the black autoformatter to keep a consistent code style.
- (#190, thanks @jrs1061) Speed up doctests
- (#165, #172, #186) Improve developer experience on Windows
- (#170, thanks @jamesscottbrown) Fix typo in comment
- (#174, #195) Add then remove autorebase workflow

## Improvements to Ringing Room Integration

- (#207) Only return 'Roll call' when Wheatley is actually able to ring.  This will hopefully
  prevent Wheatley from 'going off in a huff'.



# 0.6.0

## User-facing changes

- Load comps (including private ones) from CompLib URLs with `--comp <url>` or `-c <url>`.  Using
  CompLib IDs directly also works.
- Wheatley now calls CompLib compositions (use `--no-calls` to suppress this)
- Add proper support for backstroke starts (with 3 rows of rounds for `--up-down-in`).
- Add `--start-index` to specify how many rows into a lead of a method Wheatley should start.
- Add `-v`/`--verbose` and `-q`/`--quiet` to change how much stuff Wheatley prints.
- Print summary string of what Wheatley is going to ring before every touch, as well as how to stop
  Wheatley (i.e. using `<ctrl-C>`).
- Tell users when Wheatley is waiting for `Look To`.
- Make the error messages friendlier.
  - Moved some overly verbose `INFO` messages into `DEBUG`.
  - Capped all numbers to 3 decimal places.
  - Made debug 'wait' logging slightly less verbose.
  - Wheatley simply prints `Bye!` when interrupted with `<ctrl-C>`
- Fix broken version string (`Wheatley vv0.6.0` will now be `Wheatley v0.6.0`)

## Technical changes

- Allow support of the new tower sizes - `5`, `14` and `16`.
- Allow Wheatley to ring with any (positive) number of cover bells.
- Un-jankify error message for inputting an incorrect method title.
- Change place notation parsing to comply with CompLib and the XML specification.
- Add full static typing, and fix some `None`-related bugs.
- Reimplement the Ringing Room integration code, and fix buggy expansion of place notation when
  running on the server.
- Allow peal speed to be changed correctly whilst Wheatley is ringing.



# 0.5.3

- Prevent installing the wrong version of socketio to work with RingingRoom.

# 0.5.2

- Bump numpy version to exactly `1.19.3` on Windows to fix
  [this issue](https://tinyurl.com/y3dm3h86).

# 0.5.1

- Fix invalid initial inertia.

# 0.5.0

- Add mode for running Wheatley on a Ringing Room server.



# 0.4.0

- Corrected for Ringing Room internally changing how bells are assigned to users.
- Replaced `--max-rows-in-dataset` with `--max-bells-in-dataset` to prevent overfitting when
  Wheatley is ringing most of the bells.
- Keep Wheatley's behaviour consistent with Ringing Room's when tower sizes are changed
- Change the minimum number of bells required for regression from `2` to defaulting to `4`.
- Group CLI args into groups for better readability of both code and help messages.
- Overhaul help and debug messages to use `Wheatley` rather than `bot`.
- Added CLI arg `--name` to tell Wheatley to ring bells assigned to a specific person.
- Fix all the examples in `README.md` and add integration tests to prevent breaking them again.
- Fix `assert` being tripped by methods with an odd lead length
- Fix incorrect expansion of multiple `x`s in Place Notation

# 0.3.1

- Hopefully fixed issue of Wheatley hanging forever when `Stand next` is called.
- Re-add `--wait` flag, which does nothing but shows deprecation warning when used.
- Renamed `BOT` to `[WHEATLEY]` in the logging output for unassigned bells

# 0.3.0

- Made the `--wait` flag set by default, now has to be turned off with `--keep-going` or `-k`.
- Added overridable bobs and singles (`-b`/`--bob` for Bobs, `-n`/`--single` for Singles)
- Make default calls correct for `Grandsire` (any stage) and `Stedman` on odd stages
- Make Wheatley recognise `Plain Hunt` as a method on any stage
- Made the error messages less cryptic for the following scenaria:
  - Inputting an method name not found in the CC method library
  - Inputting the ID of a non-existent CompLib composition
  - Inputting the ID of a private CompLib composition (since private comps are not supported yet)
  - Inputting the ID of a tower that doesn't exist
  - Inputting an invalid ringing room URL
- Added a warning if you enter a method or comp which is incompatible with the number of bells in
  the tower
- The `--url` parameter will now automatically add `https://` or remove page paths if needed



# 0.2.0

- Added CLI arg for max rows stored in the regression dataset (`-X` or `--max-rows-in-dataset`)
- Added CLI arg for handstroke gap (`-G` or `--handstroke-gap`)
- Renamed shorthand for `--inertia` from `-i` to `-I` for consistency with the other regression
  args
- Fixed incorrect import when running on Windows



# 0.1.0

- Added CLI arg for peal speed (`S` or `--peal-speed`)
- Added `--version` string, which is set automatically by the GitHub Action for releasing to PyPI
- Named the bot 'Wheatley'
