"""## Executive summary (read this first)

Find the exact piecewise-linear fair-CRPS scale minimizer, with fixed median.
Use nonnegative or [0.5,2] scales; this is one-outcome hindsight, not prediction.
"""

import numpy as np
from qfbench2_common.scoring.crps import crps_ensemble


def optimal_scale(draw, truth, bounds=(0., None)):
    x = np.asarray(draw, dtype=float)
    m = float(np.median(x))
    d = x - m
    r = float(truth - m)
    # The shared toolkit supplies the spread term; scoring math is not copied.
    spread = float(np.mean(np.abs(d)) - crps_ensemble(d, 0.))
    slope = float(np.mean(-np.sign(r) * d) - spread)
    if r == 0:
        slope = float(np.mean(np.abs(d)) - spread)
        if slope < -1e-10:
            raise ValueError("Unbounded fair-CRPS scale for this degenerate ensemble")
        a = 0.
    elif slope >= 0:
        a = 0.
    else:
        mask = (d * r) > 0
        breaks = r / d[mask]
        jumps = 2 * np.abs(d[mask]) / len(d)
        order = np.argsort(breaks, kind="stable")
        crossing = np.flatnonzero(slope + np.cumsum(jumps[order]) >= -1e-14)
        if not len(crossing):
            raise ValueError("No finite scale optimum")
        a = float(breaks[order[crossing[0]]])
    lo, hi = bounds
    return float(max(lo, a) if hi is None else np.clip(a, lo, hi))


def apply(samples, truth, bounds=(0., None)):
    x = np.asarray(samples, dtype=float)
    shape = x.shape
    flat = x.reshape(len(x), -1)
    y = np.asarray(truth).reshape(-1)
    med = np.median(flat, axis=0)
    scales = np.array([optimal_scale(flat[:, j], y[j], bounds) for j in range(len(y))])
    return (med + scales * (flat - med)).reshape(shape), scales
