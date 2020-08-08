# 0.3.0
- Added overridable bobs and singles (`-b`/`--bob` for Bobs, `-n`/`--single` for Singles)
- Made the error messages nicer for the following scenaria:
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
