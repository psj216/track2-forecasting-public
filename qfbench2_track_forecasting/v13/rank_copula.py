"""Stable finite ranks and exact cellwise marginal permutation."""

import numpy as np


def percentile_ranks(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.ndim != 3 or not np.isfinite(values).all():
        raise ValueError("Expected finite [draw, horizon, asset] worlds")
    n = values.shape[0]
    order = np.argsort(values, axis=0, kind="stable")
    rank = np.empty_like(order)
    np.put_along_axis(rank, order, np.arange(n)[:, None, None], axis=0)
    return (rank + 0.5) / n


def assign_marginals(marginals: np.ndarray, ranks: np.ndarray) -> np.ndarray:
    """One source row chooses every cell's rank. Stable ties follow draw index."""
    marginal = np.asarray(marginals, dtype=float)
    if marginal.shape != ranks.shape or not np.isfinite(marginal).all():
        raise ValueError("Marginal/rank tensor mismatch")
    n = len(marginal)
    indices = np.floor(np.clip(ranks, 0, np.nextafter(1., 0.)) * n).astype(int)
    return np.take_along_axis(np.sort(marginal, axis=0, kind="stable"), indices, axis=0)
