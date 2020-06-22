"""
Module to claculate weighted regression lines of 2D data, required for the rhythm generator to work.
"""

import numpy


def fill(index, item, length):
    """
    Make an array that contains `length` 0s, but with the value at `index` replaced with `item`.
    """

    a = [0 for _ in range(length)]

    a[index] = item

    return a


def calculate_regression(data_set):
    """
    Calculates a weighted linear regression over the data given in data_set.
    Expects data_set to consist of 3-tuples of (blow_time, real_time, weight).
    """

    blow_times = [b for (b, r, w) in data_set]
    real_times = [r for (b, r, w) in data_set]
    weights = [w for (b, r, w) in data_set]

    num_datapoints = len(weights)

    x = numpy.array([[1, b] for b in blow_times])
    w = numpy.array([fill(i, w, num_datapoints) for (i, w) in enumerate(weights)])
    y = numpy.array([[x] for x in real_times])

    # Calculate (X^T * W * X) * X^T * W * y
    beta = numpy.linalg.inv(x.transpose().dot(w).dot(x)).dot(x.transpose()).dot(w).dot(y)

    return beta[0][0], beta[1][0]
