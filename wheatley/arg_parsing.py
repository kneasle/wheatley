"""
A module to contain all the functions that parse command line arguments, and their error classes.
"""

class PealSpeedParseError(ValueError):
    """
    An error thrown with a helpful error message when the user inputs a peal speed string that
    cannot be parsed by the parser.
    """

    def __init__(self, peal_spead_string, message):
        super().__init__()

        self.peal_spead_string = peal_spead_string
        self.message = message

    def __str__(self):
        return f"Error parsing peal speed '{self.peal_spead_string}': {self.message}"


def parse_peal_speed(peal_speed: str):
    """
    Parses a peal speed written in the format /2h58(m?)/ or /XXX(m?)/ into a number of minutes.
    """

    def exit_with_message(error_text):
        """ Raise an exception with a useful error message. """

        raise PealSpeedParseError(peal_speed, error_text)

    # Strip whitespace from the argument, so that if the user is in fact insane enough to pad their
    # CLI arguments with whitespace then they can do so and not crash the program.  This also has
    # the side effect of cloning the input string so we can freely modify it.
    stripped_peal_speed = peal_speed.strip()

    # Remove the 'm' from the end of the peal speed - it doesn't add any clarity
    if stripped_peal_speed.endswith("m"):
        stripped_peal_speed = stripped_peal_speed[:-1]

    if "h" in stripped_peal_speed:
        # Split the peal speed into its hour and minute components, and print a helpful message
        # if there are too many parts
        split_parts = stripped_peal_speed.split("h")

        if len(split_parts) > 2:
            exit_with_message("The peal speed should contain at most one 'h'.")

        hour_string, minute_string = split_parts

        # Strip the input values so that the user can put whitespace into the input if they want
        hour_string = hour_string.strip()
        minute_string = minute_string.strip()

        # Parse the hours value, and print messages if it is invalid
        try:
            hours = int(hour_string)
        except ValueError:
            exit_with_message(f"The hour value '{hour_string}' is not an integer.")

        if hours < 0:
            exit_with_message(f"The hour value '{hour_string}' must be a positive integer.")

        # Parse the minute value, and print messages if it is invalid
        try:
            minutes = 0 if minute_string == "" else int(minute_string)
        except ValueError:
            exit_with_message(f"The minute value '{minute_string}' is not an integer.")

        if minutes < 0:
            exit_with_message(f"The minute value '{minute_string}' must be a positive integer.")

        if minutes > 59:
            exit_with_message(f"The minute value '{minute_string}' must be smaller than 60.")

        return hours * 60 + minutes

    # If the user doesn't put an 'h' in their string, then we assume it's just a minute value that
    # may or may not be bigger than 60
    try:
        minutes = int(stripped_peal_speed)
    except ValueError:
        exit_with_message(f"The minute value '{stripped_peal_speed}' is not an integer.")

    if minutes < 0:
        exit_with_message(f"The minute value '{stripped_peal_speed}' must be a positive integer.")

    return minutes


def parse_call(input_string: str):
    """ Parse a call string into a dict of lead locations to place notation strings. """

    parsed_calls = {}

    for segment in input_string.split(","):
        # Default the location to 0 and initialise place_notation_str with None
        location = 0
        place_notation_str = None

        if ":" in segment:
            # Split the segment into location and place notations
            location_str, place_notation_str = segment.split(":")

            # Strip whitespace from the string segments so that they can be parsed more easily
            location_str = location_str.strip()
            place_notation_str = place_notation_str.strip()

            # Parse the first section as an integer
            location = int(location_str)
        else:
            # If there's only one section, it must be the place notation so all we need to do is to
            # strip it of whitespace (and `location` defaults to 0 so that's also set correctly)
            place_notation_str = segment.strip()

        # Insert the new call definition into the dictionary
        parsed_calls[location] = place_notation_str

    return parsed_calls
