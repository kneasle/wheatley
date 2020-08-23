# 0.4.0
- Replaced `--max-rows-in-dataset` with `--max-bells-in-dataset` to prevent overfitting when
  Wheatley is ringing most of the bells.
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
