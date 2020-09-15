"""
A module to contain all the functions that parse command line arguments, and their error classes.
"""

from wheatley.row_generation.place_notation_generator import PlaceNotationGenerator
from wheatley.row_generation.complib_composition_generator import ComplibCompositionGenerator, \
                                                                  PrivateCompError, InvalidCompError


class PealSpeedParseError(ValueError):
    """
    An error thrown with a helpful error message when the user inputs a peal speed string that
    cannot be parsed by the parser.
    """

    def __init__(self, peal_speed_string, message):
        super().__init__()

        self.peal_speed_string = peal_speed_string
        self.message = message

    def __str__(self):
        return f"Error parsing peal speed '{self.peal_speed_string}': {self.message}"


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


class CallParseError(ValueError):
    """
    An error thrown with a helpful error message when the user inputs a peal speed string that
    cannot be parsed by the parser.
    """

    def __init__(self, call_string, message):
        super().__init__()

        self.call_string = call_string
        self.message = message

    def __str__(self):
        return f"Error parsing call string '{self.call_string}': {self.message}"


def parse_call(input_string: str):
    """ Parse a call string into a dict of lead locations to place notation strings. """
    def exit_with_message(message):
        """ Raises a parse error with the given error message. """
        raise CallParseError(input_string, message)

    # A dictionary that will be filled with the parsed calls
    parsed_calls = {}

    for segment in input_string.split("/"):
        # Default the location to 0 and initialise place_notation_str with None
        location = 0
        place_notation_str = None

        if ":" in segment:
            # Split the segment into location and place notations
            try:
                location_str, place_notation_str = segment.split(":")
            except ValueError:
                exit_with_message(
                    f"Call specification '{segment.strip()}' should contain at most one ':'."
                )

            # Strip whitespace from the string segments so that they can be parsed more easily
            location_str = location_str.strip()
            place_notation_str = place_notation_str.strip()

            # Parse the first section as an integer
            try:
                location = int(location_str)
            except ValueError:
                exit_with_message(f"Location '{location_str}' is not an integer.")
        else:
            # If there's only one section, it must be the place notation so all we need to do is to
            # strip it of whitespace (and `location` defaults to 0 so that's also set correctly)
            place_notation_str = segment.strip()

        # Produce a nice error message if the pn string is empty
        if place_notation_str == "":
            exit_with_message("Place notation strings cannot be empty.")

        # Insert the new call definition into the dictionary
        if location in parsed_calls:
            exit_with_message(f"Location {location} has two conflicting calls: \
'{parsed_calls[location]}' and '{place_notation_str}'.")

        parsed_calls[location] = place_notation_str

    return parsed_calls


class RowGenParseError(ValueError):
    """ A class to encapsulate an error generated when parsing an RowGenerator from JSON. """
    def __init__(self, json, field, message):
        super().__init__()

        self.json = json
        self.field = field
        self.message = message

    def __str__(self):
        return f"Error parsing RowGen json '{self.json}' in field '{self.field}': {self.message}"

    def __repr__(self):
        return str(self)


def json_to_row_generator(json, logger):
    """ Takes a JSON message from SocketIO and convert it to a RowGenerator or throw an exception. """
    def raise_error(field, message, parent_error = None):
        """ A helper function to raise a `RowGenParseError` with a helpful error message. """
        if parent_error is None:
            raise RowGenParseError(json, field, message)
        raise RowGenParseError(json, field, message) from parent_error

    def json_to_call(name):
        """ Helper function to generate a call with a given name from the json. """
        if name not in json:
            logger.warning(f"No field '{name}' in the row generator JSON")
            return None

        call = {}
        for key, value in json[name].items():
            try:
                index = int(key)
            except ValueError as e:
                raise_error(name, f"Call index '{key}' is not a valid integer", e)
            call[index] = value
        return call

    if 'type' not in json:
        raise_error('type', "'type' is not defined")

    if json['type'] == 'method':
        try:
            stage = int(json['stage'])
        except KeyError as e:
            raise_error('stage', "'stage' is not defined", e)
        except ValueError as e:
            raise_error('stage', f"'{json[stage]}' is not a valid integer", e)
        return PlaceNotationGenerator(stage, "&" + json['notation'], json_to_call('bob'),
                                      json_to_call('single'))

    if json['type'] == "composition":
        try:
            comp_url = json['url']
        except KeyError as e:
            raise_error('url', "'url' is not defined", e)

        try:
            row_gen = ComplibCompositionGenerator.from_url(comp_url)
        except PrivateCompError as e:
            raise_error('complib request', "Comp id '{comp_url}' is private", e)
        except InvalidCompError as e:
            raise_error('complib request', "No composition with id '{comp_url}' found", e)
        return row_gen

    raise_error('type', f"{json['type']} is not one of 'method' or 'composition'")


def to_bool(value):
    """
    Converts a string argument to the bool representation (or throws a ValueError if the value is not
    one of '[Tt]rue' or '[Ff]alse'.
    """
    if value in ["True", "true", True]:
        return True
    if value in ["False", "false", False]:
        return False
    raise ValueError(f"Value {value} cannot be converted into a bool")
