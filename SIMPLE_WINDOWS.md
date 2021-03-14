# Simple setup for Windows

This is a short guide for installing Wheatley on Windows 10 for people who do not have much familiarity with running applications on the command line.

## Installing a Python3 environment

You need a Python3 environment in order to run Wheatley. Install the latest version from [python.org](https://www.python.org/downloads/windows/) - the first link should be to the latest build of Python3. At the bottom of the linked page is a list of downloads - most likely you need "Windows installer (64-bit)" (the recommended option).

When the file has downloaded, run it and install with defaults, ticking the "add to PATH" option on the first page. This can take a few minutes to complete.

To test this has installed correctly, you need to open a Command Prompt. Press the START button in Windows and type 'cmd' then click on the Command Prompt application.

In the Command Prompt, test the Python3 environment by typing:

```bash
py --version
```

If successful, this tell you your version number for Python.

## Installing Wheatley

With a working Python environment, you can install Wheatley by typing:

```bash
py -m pip install --upgrade wheatley
```

When this is complete, you can run Wheatley as in the [README](README.md). You will need to prefix all commands with `py -m` (see example below).

## Starting Wheatley

As a simple starter, try setting the peal speed (example here is slower than the Wheatley default) and the method like this:

```bash
py -m wheatley [ID NUMBER] --peal-speed 3h15 --method "Plain Bob Major"
```

When using the Command Prompt, you can stop a running program by typing `CTRL+C` and return to the previous command by pushing up on arrow keys.
