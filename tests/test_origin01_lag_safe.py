"""## Executive summary (read this first)

The source used at origin t is exclusively the previous business row.
"""

import numpy as np
from qfbench2_track_forecasting.origin01.engine import signal


def test_lagged_source():
    z = np.array([[0., 3.], [0., -7.], [0., 0.]])
    c = np.zeros((2, 1, 2)); c[0, 0, 1] = 2
    assert signal(c, z, 1, 0, [5])[0][0] == 2
    assert signal(c, z, 2, 0, [5])[0][0] == -10
