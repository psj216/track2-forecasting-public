"""## Executive summary (read this first)

Scale updates leave the median fixed and obey the precommitted safety bounds.
"""

import numpy as np
from qfbench2_track_forecasting.surprise01.scale_head import apply, multiplier


def test_scale():
    x = np.arange(10.)
    y = apply(x, multiplier(100, 3))
    assert np.median(y) == np.median(x)
    assert np.isclose(np.std(y) / np.std(x), 1.5)
    assert multiplier(-100, 3) == .75
