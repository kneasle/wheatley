# Wheatley
A bot for Ringing Room that can fill in any set of bells to increase the scope of potential practices.

Wheatley is designed to be a **'ninja helper with no ego'**.

He'll ring all unassigned bells perfectly whilst fitting in with whatever you are doing, adjusting to
your changes in rhythm.
He'll also never try to take control of the ringing by giving instructions or powering on with a
different rhythm to everyone else (unless you tell him to).
However, by default he'll adjust only to changes to overall rhythm – ignoring individual
bells holding up and ringing in the 'right' place regardless.

Only one ringer needs to run the command and Wheatley will ring with you after anyone calls
`Look to` in Ringing Room.
He understands all Ringing Room calls – `Go`, `Look to`, `That's all` and `Stand next` will
take effect the handstroke after they are called, and `Bob` and `Single` will result in `14` and
`1234` lead end calls.

### Notable features
- Configurable rhythm detection that updates in real time
- Automatic correction for Ringing Room using multiple server URLs for load balancing
- Very light resource footprint, as Wheatley doesn't interact with a browser to communicate with Ringing Room

### Contributing
Contributions are very welcome!  See [here](CONTRIBUTING.md) for guidance.

If you have any issues/suggestions, either
[make an issue](https://github.com/Kneasle/ringing-room-bot/issues/new), or drop me a message
[on Facebook](https://www.facebook.com/kneasle.wh.71).


## Quickstart
### Installation (using Pip)
1. Run the following command to install or update to the latest version of Wheatley:
   ```bash
   pip install --upgrade wheatley
   ```

2. Pick an example below to run Wheatley!

## Examples
Run the bot with `wheatley [ARGS]`.

*   Join a `ringingroom.com` tower with (9 digit) ID `[ID NUMBER]` and ring Plain Bob Major (tower
    bell style – wait for `Go` and `That's all`):
    ```bash
    wheatley [ID NUMBER] --method "Plain Bob Major"
    ```

*   Ring 'up, down and in' rather than waiting for 'go':
    ```bash
    wheatley --up-down-in --id [ID NUMBER] --method "Plain Bob Major"
    # or
    wheatley [ID NUMBER] -u --method "Plain Bob Major"
    ```

*   Ring full handbell style, i.e. 'up, down and in' and standing at rounds (`-H` is
    equivalent to `-us`):
    ```bash
    wheatley [ID NUMBER] --up-down-in --stop-at-rounds --method "Plain Bob Major"
    # or
    wheatley [ID NUMBER] -us --method "Plain Bob Major"
    # or
    wheatley [ID NUMBER] -H --method "Plain Bob Major"
    ```

*   Join a server other than `ringingroom.com`:
    ```bash
    wheatley [ID NUMBER] --url otherserver.com --method [METHOD TITLE]
    ```

*   Ring rows taken from a (public) composition from [complib.org](http://complib.org/), in this
    case https://complib.org/composition/65034:
    ```bash
    wheatley [ID NUMBER] --comp 65034
    ```

*   Ring at a peal speed of 3 hours 30 minutes (i.e. quite slowly):
    ```bash
    wheatley [ID NUMBER] --peal-speed 3h30
    # or
    wheatley [ID NUMBER] -S 3h30
    ```

*   Wait for people to ring rather than pushing on with the rhythm:
    ```bash
    wheatley [ID NUMBER] --method "Plain Bob Major" --wait
    ```

*   Completely ignore other users' changes in rhythm (useful if it's ringing most of
    the bells and you don't want him to randomly change speed when you make mistakes):
    ```bash
    wheatley [ID NUMBER] --method "Plain Bob Major" --inertia 1.0
    # or
    wheatley [ID NUMBER] --method "Plain Bob Major" -I 1.0
    ```

*   Print a nice help string:
    ```bash
    wheatley --help
    # or
    wheatley -h
    ```
