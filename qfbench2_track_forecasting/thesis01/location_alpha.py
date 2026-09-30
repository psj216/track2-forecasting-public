"""## Executive summary (read this first)

Fit one signed tension-to-future slope per asset and horizon using only mature
development labels. Freeze that slope before validation and final holdout.
"""

import numpy as np

MIN_PAIRS = 24
BETA_RIDGE = 0.10


def fit_beta(tension: np.ndarray, normalized_target: np.ndarray,
             mature: np.ndarray, origin_is_development: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return slopes and sample counts with shape [asset, horizon]."""
    assets = tension.shape[1]
    horizons = normalized_target.shape[2]
    beta = np.full((assets, horizons), np.nan)
    counts = np.zeros((assets, horizons), dtype=int)
    for a in range(assets):
        for h in range(horizons):
            keep = (np.isfinite(tension[:, a]) & np.isfinite(normalized_target[:, a, h])
                    & mature[:, a, h] & origin_is_development)
            counts[a, h] = keep.sum()
            if keep.sum() < MIN_PAIRS:
                continue
            x, y = tension[keep, a], normalized_target[keep, a, h]
            x = x - x.mean()
            beta[a, h] = float(np.dot(x, y - y.mean()) / (np.dot(x, x) + BETA_RIDGE * len(x)))
    return beta, counts
