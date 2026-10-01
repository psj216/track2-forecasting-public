"""## Executive summary (read this first)

Location shifts preserve all draw deviations and their ordering.
"""

import numpy as np
from qfbench2_track_forecasting.surprise01.engine import update


def test_location():
    x = np.arange(10.)
    heads, delta, _ = update(x, 2, .1, .2, 1, 5)
    np.testing.assert_allclose(heads["location"] - x, delta)
    assert np.std(heads["location"]) == np.std(x)
