"""## Executive summary (read this first)

Standardize innovations using strictly earlier same-family errors only.
Require 24 prior errors; use sample SD and a fixed five-unit clip.
"""

import numpy as np


def standardized(error, prior_errors):
    prior = np.asarray(prior_errors, dtype=float)
    prior = prior[np.isfinite(prior)]
    if len(prior) < 24:
        return None
    scale = float(np.std(prior, ddof=1))
    if scale <= 1e-12:
        return None
    return float(np.clip(error / scale, -5, 5))
