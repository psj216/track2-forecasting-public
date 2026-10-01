"""## Executive summary (read this first)

Combined equals the independent scale update followed by the same location shift.
"""

import numpy as np
from qfbench2_track_forecasting.surprise01.engine import update


def test_combined():
    x = np.arange(20.)
    out, delta, _ = update(x, -.8, .2, .3, 1, 21)
    np.testing.assert_allclose(out["combined"], out["scale"] + delta)
