"""## Executive summary (read this first)

Fit a separate no-intercept ridge model for each target and horizon. Each
target's own shock column is excluded. Lambda equals 0.1 times fit rows.
"""

import numpy as np


def fit(features, outcomes, gate, min_rows=30):
    x = np.asarray(features, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    g = np.asarray(gate, dtype=bool)
    if x.ndim != 2 or y.ndim != 3 or g.shape != y.shape[:2]:
        raise ValueError("Expected origins x sources and origins x targets x horizons")
    n_asset, n_h = y.shape[1:]
    if x.shape[1] != n_asset or x.shape[0] != y.shape[0]:
        raise ValueError("Asset and origin axes must align")
    coef = np.zeros((n_asset, n_h, n_asset))
    count = np.zeros((n_asset, n_h), dtype=int)
    events = np.zeros((n_asset, n_asset), dtype=int)
    for i in range(n_asset):
        peer = np.arange(n_asset) != i
        for j in np.flatnonzero(peer):
            events[i, j] = int(np.sum(g[:, i] & (x[:, j] != 0) & np.isfinite(x[:, j])))
        for h in range(n_h):
            valid = g[:, i] & np.isfinite(y[:, i, h]) & np.isfinite(x[:, peer]).all(axis=1)
            # A zero-shock row conveys no directional propagation information.
            valid &= (np.abs(x[:, peer]).sum(axis=1) > 0)
            count[i, h] = int(valid.sum())
            if count[i, h] < min_rows:
                continue
            a = x[valid][:, peer]
            b = y[valid, i, h]
            lam = 0.1 * count[i, h]
            coef[i, h, peer] = np.linalg.solve(a.T @ a + lam * np.eye(a.shape[1]), a.T @ b)
    return coef, count, events


def predict(coef, source, target):
    c = np.asarray(coef)[target].copy()
    c[:, target] = 0
    s = np.nan_to_num(np.asarray(source, dtype=float), nan=0.0)
    s[target] = 0
    return c @ s, c * s[None, :]
