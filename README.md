# Wheatley

[![PyPI version](https://badge.fury.io/py/wheatley.svg)](https://badge.fury.io/py/wheatley)
![Tests and Linting](https://github.com/Kneasle/wheatley/workflows/Tests%20and%20Linting/badge.svg)

A bot for [Ringing Room](https://ringingroom.com/) that can fill in any set of bells to increase the
scope of potential practices, designed to be a **'ninja helper with no ego'**.

If you just want to use Wheatley for normal ringing without caring about how it works, then check
out how to use Wheatley directly [inside Ringing Room](https://ringingroom.com/help#wheatley) - no
installation required, just a flick of a switch.  If you want more control than the Ringing Room
interface provides or are interested in how Wheatley works, then this is the place to go.  This
repository contains Wheatley's source code, and documentation of the 'classic' command line version.

## Contributing

Contributions are very welcome!  To keep this readme short, all contribution info is in
[CONTRIBUTING.md](CONTRIBUTING.md).  If you have any issues/suggestions, either [make an
issue](https://github.com/kneasle/wheatley/issues/new), or drop me a message [on
Facebook](https://www.facebook.com/kneasle.wh.71).

## Quickstart

_(This quickstart refers to the command-line Wheatley, not the integrated version)_.  Also, if
anything here doesn't work or is confusing, please let us know.  For help with what parameters
Wheatley has and what they do, run `wheatley --help`.

### Step 1: Install Python

Installation is very platform specific, so I've split this by OS.

#### Windows

1. Download the latest version of Python from
   [python.org](https://www.python.org/downloads/windows/) - the first link should be to the latest
   build of Python 3. At the bottom of the linked page is a list of downloads - most likely you need
   "Windows installer (64-bit)" (the recommended option).
2. When the file has downloaded, run it.  Before starting the installation, **tick the "Add to
   PATH" option** (this will make your life way easier later on).  Start the install, and then wait
   for it to complete.
3. In order to run Wheatley, you'll need to open a 'command prompt'.  To do this, press the START
   button in Windows, type 'cmd' then click on the `Command Prompt` application.  This creates a
   black window, into which you can type and then run commands (including Wheatley).
4. Test Python by typing `py --version` and then pressing enter.  If all is well, this will print a
   version string - otherwise something has gone wrong.

#### MacOS

Instructions should be [here](https://docs.python-guide.org/starting/install3/osx/).

#### Linux

Almost all Linux distros come with Python installed, so this step can probably be skipped.

### Step 2: Install Wheatley

Once Python is installed, installing Wheatley should be done through Python's package manager `pip`.
The exact commands vary from system to system (and I can't keep track of them all), but one of the
following should work:

```bash
# Should work on Windows
py -m pip install --upgrade wheatley
# Should work on MacOS and Linux
python3 -m pip install --upgrade wheatley
```

### Step 3: Run Wheatley

**NOTE:** The name of the Wheatley command will sometimes vary.  If you're getting errors like
'wheatley not found', then try replacing the `wheatley` prefix with `py -m wheatley` (Windows) or
`python3 -m wheatley` (MacOS/Linux).  So therefore, a complete command would look like:
```
py -m wheatley [ID NUMBER] --method "Plain Bob Major"
# or 
python3 -m wheatley [ID NUMBER] --method "Plain Bob Major"
```

## Examples

*   Join a `ringingroom.com` tower with (9 digit) ID `[ID NUMBER]` and ring Plain Bob Major (tower
    bell style – wait for `Go` and `That's all`):
    ```bash
    wheatley [ID NUMBER] --method "Plain Bob Major"
    ```

*   Ring 'up, down and in' rather than waiting for 'go':
    ```bash
    wheatley [ID NUMBER] --use-up-down-in --method [METHOD TITLE]
    # or
    wheatley [ID NUMBER] -u --method [METHOD TITLE]
    ```

*   Ring full handbell style, i.e. 'up, down and in' and standing at rounds (`-H` is
    equivalent to `-us`):
    ```bash
    wheatley [ID NUMBER] --use-up-down-in --stop-at-rounds --method [METHOD TITLE]
    # or
    wheatley [ID NUMBER] -us --method [METHOD TITLE]
    # or
    wheatley [ID NUMBER] -H --method [METHOD TITLE]
    ```

*   Join a server other than `ringingroom.com`:

    <!--- doctest-ignore -->
    ```bash
    wheatley [ID NUMBER] --url otherwebsite.com --method [METHOD TITLE]
    ```

*   Ring rows and make calls taken from a composition from [complib.org](http://complib.org/), in this
    case https://complib.org/composition/65034:
    ```bash
    wheatley [ID NUMBER] --comp 65034
    ```
*   Ring rows but don't send the calls to Ringing Room taken from a composition from [complib.org](http://complib.org/), in this
    case https://complib.org/composition/65034:
    ```bash
    wheatley [ID NUMBER] --comp 65034 --no-calls
    ```

*   Ring compositions with **substituted methods** by copying the id and query string or full url from [complib.org](http://complib.org/)):
    ```bash
     wheatley [ID NUMBER] --comp 68549?substitutedmethodid=28000
     # or 
     wheatley [ID NUMBER] --comp https://complib.org/composition/68549?substitutedmethodid=28000
    ```
*   Ring **private** compositions by copying the share link from [complib.org](http://complib.org/):
    ```bash
     wheatley [ID NUMBER] --comp 51155?accessKey=9e1fcd2b11435552cf236be93c7ff73058870995
     # or
     wheatley [ID NUMBER] --comp https://complib.org/composition/51155?accessKey=9e1fcd2b11435552cf236be93c7ff73058870995
    ```
* Combine method substitution and private composition
    <!--- doctest-ignore -->
    ```bash
     wheatley [ID NUMBER] --comp 51155?substitutedmethodid=27600&accessKey=9e1fcd2b11435552cf236be93c7ff73058870995
    ```

*   Ring rows specified by place notation, in this case Plain Bob Minor:
    ```bash
    wheatley [ID NUMBER] --place-notation 6:x16x16x16,12
    ```

*   Ring at a peal speed of 3 hours 30 minutes (i.e. quite slowly):
    ```bash
    wheatley [ID NUMBER] --method [METHOD TITLE] --peal-speed 3h30
    # or
    wheatley [ID NUMBER] --method [METHOD TITLE] -S 3h30
    ```

*   Make Wheatley push on with the rhythm rather than waiting for people to ring.
    ```bash
    wheatley [ID NUMBER] --method [METHOD TITLE] --keep-going
    # or
    wheatley [ID NUMBER] --method [METHOD TITLE] -k
    ```

*   Completely ignore other users' changes in rhythm (useful if he's ringing most of
    the bells and you don't want him to randomly change speed when you make mistakes):
    ```bash
    wheatley [ID NUMBER] --method [METHOD TITLE] --inertia 1.0
    # or
    wheatley [ID NUMBER] --method [METHOD TITLE] -I 1.0
    ```
*   Start from a different row
    ``` bash
    wheatley [ID NUMBER] --method [METHOD TITLE] --start-row 13572468
    ```
