"""## Executive summary (read this first)

Describe historical fit coverage without selecting edges or changing the model.
These exposed years are structural diagnostics rather than independent evidence.
"""

import numpy as np


def coverage(training):
    d = np.load(training)
    years = d["dates"].astype("datetime64[Y]").astype(int) + 1970
    return {str(y): {"origins": int((years == y).sum()),
                     "mature_cells": int(np.isfinite(d["q"][years == y]).sum()),
                     "shock_origins": int((np.abs(d["source"][years == y]).sum(axis=1) > 0).sum())}
            for y in np.unique(years)}
