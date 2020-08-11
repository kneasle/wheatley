""" Utils for the fuzzing code. """

def fuzz_for_unwrapped_errors(function_to_fuzz,
                              input_generation_function,
                              expected_error,
                              iterations=10000):
    """ Fuzz a given function with generated input, checking for a given error. """

    errors_found = 0

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

            print(f"Error type '{error_type}' thrown on input '{generated_input}': '{e}'.")

            errors_found += 1

            if errors_found > 10:
                return

    if errors_found == 0:
        print(f"{iterations} iterations were run, and they all threw the right error class.")
