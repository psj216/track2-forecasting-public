"""## Executive summary (read this first)

Each daily innovation is divided by a trailing 252-observation standard deviation.
The scale at t is shifted one row, so it uses only dates strictly before t.
"""

import numpy as np
import pandas as pd

WINDOW = 252
MIN_OBSERVATIONS = 200
FLOOR = 1e-8
CLIP = 8.0


def scaled(steps: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sigma = steps.rolling(WINDOW, min_periods=MIN_OBSERVATIONS).std().shift(1).clip(lower=FLOOR)
    z = (steps / sigma).clip(-CLIP, CLIP).replace([np.inf, -np.inf], np.nan)
    return z, sigma
