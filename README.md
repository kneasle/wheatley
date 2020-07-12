# Ringing Room Bot
A bot for Ringing Room that can fill in any set of bells to increase the scope of potential practices.

This bot is designed to be a **'ninja helper with no ego'**.

It will ring unassigned bells perfectly whilst fitting into whatever you are doing, adjusting to
your changes in rhythm.
It will never try to take control of the ringing by giving instructions or powering on with a
different rhythm to everyone else (unless you tell it to).
However, by default it will adjust only to changes to overall rhythm - it will ignore individual
bells holding up and ring in the 'right' place regardless.

It's also very easy to use - run the command and it will ring with you after anyone calls
`Look to` in Ringing Room.
It understands `Go`, `Look to`, `That's all` and `Stand next` in Ringing Room, but currently can only
ring plain courses of any given method (or touches from CompLib).

### Notable features
- Configurable rhythm detection that updates in real time
- Automatic correction for Ringing Room using multiple server URLs for load balancing
- Very light resource footprint, as it doesn't interact with a browser to talk to Ringing Room

### Roadmapped features
- Make the bot able to ring touches of methods

## Quickstart
### Installation (same for all platforms if using the command line)
1. Clone and download this repository (using [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) will make updating easier):
   ```bash
   git clone https://github.com/Kneasle/ringing-room-bot
   ```
   (you can update the bot at any time with `git pull origin master`)

2. Make sure you have Python 3.x installed with:
   ```bash
   python3 --version
   ```
   If Python 3.x is installed it will print the version and if Python 3.x isn't installed it will produce an error.
   
3. Move to the location of the repository:
   ```bash
   cd [REPOSITORY LOCATION]
   ```

4. Install the required python packages:
   ```bash
   pip3 install -r requirements.txt
   ```

5. Pick an example below to run the bot!

## Examples
Run the bot with `python3 main.py [args]` (or `./main.py [args]` on Unix).
You may have to use `python` instead of `python3` on Windows.

*   Join a `ringingroom.com` tower with id `[ID]` and ring Plain Bob Major (tower bell style):
    ```bash
    python3 main.py --id [ID] --method "Plain Bob Major"
    ```

*   Make the bot ring up-down-in rather than waiting for 'go':
    ```bash
    python3 main.py --up-down-in --id [ID] --method "Plain Bob Major"
    # or
    python3 main.py -u --id [ID] --method "Plain Bob Major"
    ```

*   Make the bot ring full handbell style, i.e. up-down-in and standing at rounds (`-H` is equivalent to `-us`):
    ```bash
    python3 main.py --up-down-in --stop-at-rounds --id [ID] --method "Plain Bob Major"
    # or
    python3 main.py -us --id [ID] --method "Plain Bob Major"
    # or
    python3 main.py -H --id [ID] --method "Plain Bob Major"
    ```

*   Join a server other than `ringingroom.com`:
    ```bash
    python3 main.py --id [ID] --url otherserver.com
    ```

*   Ring rows taken from a (public) Complib composition, in this case https://complib.org/composition/65034:
    ```bash
    python3 main.py --id [ID] --comp 65034
    ```

*   Make the bot wait for people to ring rather than pushing on with the rhythm:
    ```bash
    python3 main.py --id [ID] --method "Plain Bob Major" --wait
    ```

*   Make the bot completely ignore other users' changes in rhythm (useful if it's ringing most of
    the bells and you don't want it to randomly change speed when you make mistakes):
    ```bash
    python3 main.py --id [ID] --method "Plain Bob Major" --inertia 1.0
    # or
    python3 main.py --id [ID] --method "Plain Bob Major" -i 1.0
    ```

*   Print a nice help string:
    ```bash
    python3 main.py --help
    # or
    python3 main.py -h
    ```
