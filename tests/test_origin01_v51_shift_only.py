"""## Executive summary (read this first)

Every draw receives the same location increment, preserving ranks and tails.
"""

import numpy as np
from qfbench2_track_forecasting.origin01.engine import forecast


def test_location_only():
    x = np.arange(50.).reshape(10, 5)
    y, shifts = forecast(x, np.ones(5), 2, [5, 21, 63, 126, 189])
    np.testing.assert_allclose(y-x, np.broadcast_to(shifts, x.shape))
    np.testing.assert_allclose(np.std(y, axis=0), np.std(x, axis=0))
