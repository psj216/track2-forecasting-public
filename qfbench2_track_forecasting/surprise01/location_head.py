"""## Executive summary (read this first)

Every V5.1 draw gets exactly the same surprise-conditioned location shift.
"""

import numpy as np


def shift(beta, surprise, sigma, horizon):
    return float(beta * surprise * sigma * np.sqrt(horizon))


def apply(draws, delta):
    return np.asarray(draws, float) + delta
