"""## Executive summary (read this first)

Break chronological tension and the learned market-to-peer mapping in two fixed
controls. Both controls must be evaluated on the same V5.1 draws and labels.
"""

import numpy as np

from qfbench2_track_forecasting.thesis01.tension import at

SEED = 4101


def time_shuffle(signal: np.ndarray, origins: np.ndarray) -> np.ndarray:
    out = signal.copy()
    rng = np.random.default_rng(SEED)
    years = origins.astype("datetime64[Y]").astype(int) + 1970
    for a in range(signal.shape[1]):
        for start, end in ((2001, 2013), (2013, 2018), (2018, 2024)):
            rows = np.flatnonzero((years >= start) & (years < end) & np.isfinite(signal[:, a]))
            out[rows, a] = signal[rng.permutation(rows), a]
    return out


def peer_permutation(z: np.ndarray, grid_rows: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    ranks = rng.permutation(z.shape[1])
    result = np.full((len(grid_rows), z.shape[1]), np.nan)
    for i, row in enumerate(grid_rows):
        result[i] = at(z, int(row), lag=1, peer_order=ranks)
    return result
