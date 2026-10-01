"""## Executive summary (read this first)

Mutating all rows after t cannot change the origin-t signal or forecast.
"""

import numpy as np
from qfbench2_track_forecasting.origin01.engine import signal, forecast


def test_future_mutation():
    c = np.ones((3, 2, 3))
    z = np.array([[3., 0., -4.], [0., 0., 0.], [0., 2., 0.], [5., 4., 3.]])
    before = signal(c, z, 1, 1, [5, 21])
    altered = z.copy(); altered[2:] = 1e8
    after = signal(c, altered, 1, 1, [5, 21])
    np.testing.assert_array_equal(before[0], after[0])
    draws = np.arange(20.).reshape(10, 2)
    np.testing.assert_array_equal(forecast(draws, before[0], 2, [5, 21])[0],
                                  forecast(draws, after[0], 2, [5, 21])[0])
