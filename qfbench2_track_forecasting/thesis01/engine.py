"""## Executive summary (read this first)

The engine computes cutoff-safe tension and applies a frozen signed location
slope to V5.1 draws. The V12/V13 model outputs are never used as predictors.
"""

from dataclasses import dataclass

import numpy as np

from .tension import at
from .v51_shift import shift_only


@dataclass(frozen=True)
class Thesis01Engine:
    z: np.ndarray
    sigma: np.ndarray
    beta: np.ndarray

    def forecast(self, row: int, asset: int, horizon: int, horizon_index: int,
                 baseline: np.ndarray, *, lag: int = 1) -> np.ndarray:
        signal = at(self.z, row, lag=lag)[asset]
        slope = self.beta[asset, horizon_index]
        scale = self.sigma[row, asset]
        if not np.isfinite([signal, slope, scale]).all():
            return np.asarray(baseline).copy()
        return shift_only(baseline, slope, signal, scale, horizon)
