"""Frozen Student-t radial law; no runtime calibration."""

import numpy as np


def radial(rng: np.random.Generator, df: float, size: tuple[int, ...]) -> np.ndarray:
    return rng.standard_t(df, size=size) * np.sqrt((df - 2.) / df)


def estimate_df(residual: np.ndarray) -> float:
    z = residual[np.isfinite(residual)]
    if len(z) < 10:
        return 8.
    sd = max(float(np.std(z)), 1e-8)
    excess = max(float(np.mean(((z - np.mean(z)) / sd) ** 4) - 3), 0.01)
    return float(np.clip(6 / excess + 4, 4.1, 30.))
