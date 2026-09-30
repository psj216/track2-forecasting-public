"""## Executive summary (read this first)

Estimate a 504-day linear conditional market value with fixed diagonal shrinkage.
For each target, its current value is excluded from its own predictors. A second,
separately fitted model uses peer values one business row earlier.
"""

import numpy as np

WINDOW = 504
MIN_HISTORY = 252
SHRINKAGE = 0.10


def implied_at(z: np.ndarray, row: int, lag: int = 0,
               peer_order: np.ndarray | None = None) -> np.ndarray:
    """Return implied Z at row; only rows < row fit the conditional model.

    Missing historical standardized innovations are mapped to zero (their ex-ante
    expected increment). Assets with fewer than 252 observations in the window
    do not participate. peer_order permutes the peer-to-column mapping for the
    negative control and never alters the target series.
    """
    if row < MIN_HISTORY + lag:
        return np.full(z.shape[1], np.nan)
    start = max(lag, row - WINDOW)
    historical = z[start:row]
    eligible = np.sum(np.isfinite(historical), axis=0) >= MIN_HISTORY
    ids = np.flatnonzero(eligible)
    result = np.full(z.shape[1], np.nan)
    if len(ids) < 3:
        return result
    y = np.nan_to_num(historical[:, ids], nan=0.0)
    x = np.nan_to_num(z[start - lag:row - lag, :][:, ids], nan=0.0)
    present = np.nan_to_num(z[row - lag, ids], nan=0.0)
    xm, ym = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - xm, y - ym
    cov = xc.T @ xc / len(x)
    ridge = SHRINKAGE * np.trace(cov) / len(ids) + 1e-4
    precision = np.linalg.inv(cov + np.eye(len(ids)) * ridge)
    full = (yc.T @ xc / len(x)) @ precision
    # Frisch-Waugh leave-one-column-out identity. The predictor corresponding
    # to the target is excluded even for the permuted negative control.
    off = full - full.diagonal()[:, None] * (precision / precision.diagonal()[:, None])
    np.fill_diagonal(off, 0.0)
    if peer_order is None:
        result[ids] = ym + off @ (present - xm)
    else:
        # Permute current OTHER-market values after fitting the unpermuted
        # conditional model. Refitting a linear model after merely renaming its
        # columns would leave predictions unchanged and is not a valid control.
        ranks = np.asarray(peer_order)
        for i in range(len(ids)):
            others = np.flatnonzero(np.arange(len(ids)) != i)
            perm = others[np.argsort(ranks[ids[others]], kind="mergesort")]
            result[ids[i]] = ym[i] + off[i, others] @ (present[perm] - xm[others])
    result[ids[~np.isfinite(z[row, ids])]] = np.nan
    return result
