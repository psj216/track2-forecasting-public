"""## Executive summary (read this first)

Even a nonzero diagonal in a loaded artifact cannot predict from self shock.
"""

import numpy as np
from qfbench2_track_forecasting.origin01.propagation_model import fit, predict


def test_self_excluded_in_fit_and_inference():
    x = np.tile([3., 2.], (40, 1))
    y = np.ones((40, 2, 1))
    c, _, _ = fit(x, y, np.ones((40, 2), bool))
    assert c[0, 0, 0] == c[1, 0, 1] == 0
    c[0, 0, 0] = 1e6
    assert predict(c, [3, 0], 0)[0][0] == 0
