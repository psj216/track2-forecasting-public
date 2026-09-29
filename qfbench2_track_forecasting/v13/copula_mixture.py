"""Precommitted 70/30 whole-draw source choice in common percentile units."""

import numpy as np


def mix(v51_percentiles: np.ndarray, bank_percentiles: np.ndarray,
        seed: int, v51_weight: float = 0.7) -> np.ndarray:
    if v51_percentiles.shape != bank_percentiles.shape:
        raise ValueError("Copula sources must be aligned")
    rng = np.random.default_rng(seed)
    selector = rng.random(len(v51_percentiles)) < v51_weight
    return np.where(selector[:, None, None], v51_percentiles, bank_percentiles)
