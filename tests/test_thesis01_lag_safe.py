"""## Executive summary (read this first)

Lag-safe prediction excludes other assets' same-day innovations.
"""
import numpy as np
from qfbench2_track_forecasting.thesis01.tension import at


def test_other_current_values_do_not_change_lag_signal():
    rng = np.random.default_rng(7)
    z = rng.normal(size=(530, 4))
    before = at(z, 520, lag=1)[0]
    z[520, 1:] = 100000
    assert at(z, 520, lag=1)[0] == before
