"""## Executive summary (read this first)

A target is eligible only when today's own standardized move is below one.
Missing observations cannot pass the gate.
"""

import numpy as np


def unreacted(z):
    x = np.asarray(z, dtype=float)
    return np.isfinite(x) & (np.abs(x) < 1.0)
