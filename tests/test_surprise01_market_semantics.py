"""## Executive summary (read this first)

Levels use endpoint differences; log-return increments accumulate after origin.
"""

import numpy as np
import pandas as pd
from qfbench2_track_forecasting.v12.data_parity import _label


def test_target_representation():
    dates = pd.bdate_range("2020-01-01", periods=10)
    s = pd.Series(np.arange(10.), index=dates)
    assert _label(s, "level", dates[0], 5, "2100-01-01", False)[0] == 5
    assert _label(s, "log_return", dates[0], 5, "2100-01-01", False)[0] == 15
