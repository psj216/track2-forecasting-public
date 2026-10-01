"""## Executive summary (read this first)

Only an absolute standardized innovation of at least two is a source shock.
The signal is its signed excess above two, capped by the upstream eight-unit clip.
"""

import numpy as np

THRESHOLD = 2.0


def excess(z):
    x = np.asarray(z, dtype=float)
    return np.where(np.isfinite(x), np.sign(x) * np.maximum(np.abs(x) - THRESHOLD, 0), 0.0)
