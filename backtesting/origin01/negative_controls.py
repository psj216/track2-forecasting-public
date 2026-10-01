"""## Executive summary (read this first)

Shuffle source event dates or misassign source names only at inference.
The name permutation acts after fitting; a consistent relabeling of both
training and evaluation columns would leave ridge forecasts identical.
"""

import numpy as np

from qfbench2_track_forecasting.origin01.propagation_model import predict
from qfbench2_track_forecasting.origin01.unreacted_gate import unreacted


def source_controls(source_matrix, seed=1901):
    rng = np.random.default_rng(seed)
    x = np.asarray(source_matrix)
    return x[rng.permutation(len(x))], np.roll(x, 1, axis=1)


def controlled(coef, source, z_target, target, kind):
    s = np.asarray(source).copy()
    if kind == "peer_permuted":
        # Permute the 24 peers, never introduce self as a source.
        peer = np.flatnonzero(np.arange(len(s)) != target)
        old = s.copy()
        s[peer] = np.roll(old[peer], 1)
        s[target] = 0
    alpha, _ = predict(coef, s, target)
    return alpha * bool(unreacted(z_target))
