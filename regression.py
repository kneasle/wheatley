import numpy


def fill(index, item, length):
    a = [0 for _ in range(length)]

    a[index] = item

    return a


def calculate_regression(data_set):
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
