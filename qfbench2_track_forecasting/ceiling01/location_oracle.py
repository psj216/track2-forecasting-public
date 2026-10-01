"""## Executive summary (read this first)

Translate every cell to its outcome; preserve deviations and ranks.
"""

import numpy as np


def apply(samples, truth):
    x = np.asarray(samples, dtype=float)
    return x + (np.asarray(truth) - np.median(x, axis=0))
