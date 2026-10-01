"""## Executive summary (read this first)

Call existing scoring primitives and reproduce V13's research aggregation.
This is RESEARCH_PROXY_ONLY: baseline-relative scales are not sealed ref_scale.
"""

import numpy as np
from qfbench2_common.scoring import crps
from qfbench2_track_forecasting.scoring import _composite

COMPONENTS = ("marginal", "joint", "tail")
LEVELS = (.01, .05, .95, .99)


def weights(cells):
    return np.array([.5, .3, .2]) if cells > 1 else np.array([5/7, 0., 2/7])


def components(samples, truth):
    x = np.asarray(samples, dtype=float).reshape(len(samples), -1)
    y = np.asarray(truth, dtype=float).reshape(-1)
    if x.shape[1] != len(y) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Missing or invalid cell: no silent dropping or imputation")
    return _composite(x, y, weights=tuple(weights(len(y))), tail_levels=LEVELS,
                      joint="variogram", tail_metric="pinball", ref_scale=None)


def composite_from_components(values, reference, cells):
    # Identical denominators and single-cell redistribution to evaluate_proxy.py.
    terms = [float(values[k]) / max(float(reference[k]), 1e-12) for k in COMPONENTS]
    return float(weights(cells) @ terms)


def score(samples, truth, reference):
    comp = components(samples, truth)
    return {**comp, "ratio": composite_from_components(comp, reference, np.size(truth))}


def aggregate(values):
    if not values:
        return None
    # Reproduce the actual V13 research floor, including zero-loss substitutions.
    return float(np.exp(np.mean(np.log(np.maximum(values, 1e-12)))))


def marginal_cells(samples, truth):
    return np.asarray(crps.crps_ensemble(samples, truth), dtype=float)
