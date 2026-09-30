"""## Executive summary (read this first)

Tension is the observed standardized target innovation minus its market-implied
value. Its sign is descriptive; no mean-reversion direction is imposed.
"""

import numpy as np

from .implied_value import implied_at


def at(z: np.ndarray, row: int, lag: int = 0,
       peer_order: np.ndarray | None = None) -> np.ndarray:
    return z[row] - implied_at(z, row, lag, peer_order)
