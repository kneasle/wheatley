# Ringing Room Bot
A bot for Ringing Room that can fill in any set of bells to increase the scope of potential practices.

This bot is designed to be a **'ninja helper with no ego'**.

It will ring all unassigned bells perfectly whilst fitting in with whatever you are doing, adjusting to
your changes in rhythm.
It will never try to take control of the ringing by giving instructions or powering on with a
different rhythm to everyone else (unless you tell it to).
However, by default it will adjust only to changes to overall rhythm - it will ignore individual
bells holding up and ring in the 'right' place regardless.

Only one ringer needs to run the command and it will ring with you after anyone calls `Look to` in
Ringing Room.
It will understand all Ringing Room calls - `Go`, `Look to`, `That's all` and `Stand next` will
take effect the handstroke after they are called, and `Bob` and `Single` will result in `14` and
`1234` lead end calls.

### Notable features
- Configurable rhythm detection that updates in real time
- Automatic correction for Ringing Room using multiple server URLs for load balancing
- Very light resource footprint, as it doesn't interact with a browser to communicate with Ringing Room

### Contributing
Contributions are very welcome!  See [here](CONTRIBUTING.md) for guidance.

If you have any issues/suggestions, either
[make an issue](https://github.com/Kneasle/ringing-room-bot/issues/new), or drop me a message
[on Facebook](https://www.facebook.com/kneasle.wh.71).


## Quickstart
### Installation (using Pip)
1. Run the following command to install or update to the latest version of the bot:
   ```bash
   pip3 install --upgrade rr-bot
   ```
   (use `pip install --upgrade rr-bot` on Windows).

2. Pick an example below to run the bot!

## Examples
Run the bot with `rr-bot [ARGS]`.

*   Join a `ringingroom.com` tower with (9 digit) id `[ID NUMBER]` and ring Plain Bob Major (tower
    bell style - wait for `Go` and `That's all`):
    ```bash
    rr-bot [ID NUMBER] --method "Plain Bob Major"
    ```

*   Make the bot ring 'up, down and in' rather than waiting for 'go':
    ```bash
    rr-bot --up-down-in --id [ID NUMBER] --method "Plain Bob Major"
    # or
    rr-bot [ID NUMBER] -u --method "Plain Bob Major"
    ```

*   Make the bot ring full handbell style, i.e. 'up, down and in' and standing at rounds (`-H` is
    equivalent to `-us`):
    ```bash
    rr-bot [ID NUMBER] --up-down-in --stop-at-rounds --method "Plain Bob Major"
    # or
    rr-bot [ID NUMBER] -us --method "Plain Bob Major"
    # or
    rr-bot [ID NUMBER] -H --method "Plain Bob Major"
    ```

*   Join a server other than `ringingroom.com`:
    ```bash
    rr-bot [ID NUMBER] --url otherserver.com --method [METHOD TITLE]
    ```

*   Ring rows taken from a (public) composition from [complib.org](http://complib.org/), in this
    case https://complib.org/composition/65034:
    ```bash
    rr-bot [ID NUMBER] --comp 65034
    ```

*   Make the bot wait for people to ring rather than pushing on with the rhythm:
    ```bash
    rr-bot [ID NUMBER] --method "Plain Bob Major" --wait
    ```

*   Make the bot completely ignore other users' changes in rhythm (useful if it's ringing most of
    the bells and you don't want it to randomly change speed when you make mistakes):
    ```bash
    rr-bot [ID NUMBER] --method "Plain Bob Major" --inertia 1.0
    # or
    rr-bot [ID NUMBER] --method "Plain Bob Major" -i 1.0
    ```

*   Print a nice help string:
    ```bash
    rr-bot --help
    # or
    rr-bot -h
    ```
