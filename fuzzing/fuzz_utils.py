""" Utils for the fuzzing code. """

class FuzzingError(ValueError):
    """ A custom error used to signal that some un-abstracted errors were found. """

    def __init__(self, function_name, errors_found):
        super().__init__()

        self._function_name = function_name
        self._errors_found = errors_found

    def __str__(self):
        error_messages = "\n  ".join(self._errors_found)

        return f"'{self._function_name}' threw uncaught errors:\n{error_messages}"


def fuzz_for_unwrapped_errors(function_name,
                              function_to_fuzz,
                              input_generation_function,
                              expected_error,
                              iterations=100000):
    """ Fuzz a given function with generated input, checking for a given error. """

    errors_found = []

    for _ in range(iterations):
        generated_input = input_generation_function()

        try:
            function_to_fuzz(generated_input)
        except expected_error:
            pass
        except Exception as e:
            error_type = str(type(e))

            if "'" in error_type:
                error_type = error_type.split("'")[1]

            errors_found.append(
                f"Error type '{error_type}' thrown on input '{generated_input}': '{e}'."
            )

            if len(errors_found) > 10:
                break

    if len(errors_found) == 0:
        print(f"{iterations} iterations were run on {function_name}, and they all threw the right \
error class.")
    else:
        raise FuzzingError(function_name, errors_found)
