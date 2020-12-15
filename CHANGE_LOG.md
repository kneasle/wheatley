# 0.6.0 (W.I.P.)
- Print summary string of what Wheatley is going to ring.
- Tell users when Wheatley is waiting for `Look To`.
- Allow support of the new tower sizes - `5`, `14` and `16`.
- Change place notation parsing to comply with CompLib and the XML specification.
- Allow Wheatley to ring with any (positive) number of cover bells.
- Add full static typing, and fix some `None`-related bugs.
- Prevent installing the wrong version of socketio to work with RingingRoom

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
- Renamed the bot to Wheatley
