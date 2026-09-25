"""Leakage-safe monotone tail calibration primitives for Numeric V3 experiments."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def calibrate_single_cell_tails(
    samples: NDArray[np.float64], lower: float = 1.0, upper: float = 1.0
) -> NDArray[np.float64]:
    """Scale only observations outside Q10/Q90 while preserving the central 80% exactly.

    The transform is intentionally limited to one asset and one horizon. Calibration factors
    must be selected on a historical fit split before any later holdout is examined.
    """
    if not all(np.isfinite(x) and 0.75 <= x <= 1.25 for x in (lower, upper)):
        raise ValueError("tail factors must be finite and in [0.75, 1.25]")
    if samples.ndim != 3:
        raise ValueError("samples must have shape [draw, asset, horizon]")
    if samples.shape[1:] != (1, 1) or (lower == 1.0 and upper == 1.0):
        return samples.copy()

    lo, hi = np.quantile(samples, [0.10, 0.90], axis=0)
    result = np.where(samples < lo, lo + lower * (samples - lo), samples)
    result = np.where(result > hi, hi + upper * (result - hi), result)
    return np.asarray(result, dtype=np.float64)
