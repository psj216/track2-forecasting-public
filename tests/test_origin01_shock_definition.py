"""## Executive summary (read this first)

The sole frozen shock threshold is two standard deviations of signed excess.
"""

import numpy as np
from qfbench2_track_forecasting.origin01.shock_detector import excess


def test_signed_excess():
    np.testing.assert_allclose(excess([-8, -4, -2, -1.9, 0, 2, 2.3, 4, np.nan]),
                               [-6, -2, 0, 0, 0, 0, .3, 2, 0])
