"""## Executive summary (read this first)

Scale deviations around the unchanged median. Bound multiplier to [0.75,1.50].
"""

import numpy as np


def multiplier(gamma, surprise):
    return float(np.exp(np.clip(gamma * abs(surprise), np.log(.75), np.log(1.50))))


def apply(draws, factor):
    x = np.asarray(draws, float)
    median = np.median(x)
    return median + factor * (x - median)
