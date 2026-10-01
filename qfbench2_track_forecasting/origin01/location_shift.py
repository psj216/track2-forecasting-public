"""## Executive summary (read this first)

Add exactly one shared native shift to every V5.1 draw for a target/horizon.
"""

import numpy as np


def native_shift(normalized_alpha, sigma, horizon):
    return float(normalized_alpha * sigma * np.sqrt(horizon))


def apply(draws, shift):
    return np.asarray(draws, dtype=float) + shift
