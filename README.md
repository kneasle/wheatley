# Ringing Room Bot
A bot for Ringing Room that can fill in any set of bells to increase the scope of potential practices

## Current features
- Will anonymously ring any unassigned bells to plain courses of any method or any composition on CompLib (amongst other things).
- Can detect and compenstate for changes in ringing speed made by the human ringers.
- Adjustable sensitivity to speed changes (can be set to completely ignore other people), as well as adjustable pulloff speed (for when the bot is ringing both 1 and 2) and handstroke gap sizes.
- Will respond to "Look to", "That's all", "Go", and "Stand" at the next handstroke after the call.

## Quickstart
### Installation (same for all platforms if using the command line)
1. Clone and download this repository.

2. Make sure you have Python 3.x installed with:
   ```bash
   python3 --version
   ```
   If Python 3.x is installed it will print the version and if python 3.x isn't installed it will produce an error.
   
3. Move to the location of the repository:
   ```bash
   cd <repository location>
   ```

4. Install the required python packages:
   ```bash
   pip3 install -r requirements.txt
   ```
5. Start the bot with the following command, replacing `Plain Bob Major` with the title of the method you want to ring:
   ```bash
   python3 main.py --id <ringing room tower id> --method "Plain Bob Major"
   ```
On Unix you can run main.py directly:
```bash
./main.py --id <ringing room tower id> --method "Plain Bob Major"
```

For a list of options, you can run the bot with the `--help` or `-h` argument.
