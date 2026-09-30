"""## Executive summary (read this first)

The peer-mapping control actually breaks the fitted cross-market mapping.
"""
import numpy as np
from qfbench2_track_forecasting.thesis01.implied_value import implied_at
from backtesting.thesis01.negative_controls import time_shuffle


def test_peer_and_time_controls_change_signals():
    rng = np.random.default_rng(4101)
    z = rng.normal(size=(600, 8))
    assert not np.array_equal(implied_at(z, 550),
                              implied_at(z, 550, peer_order=rng.permutation(8)))
    signal = rng.normal(size=(30, 3))
    years = np.array(["2005-01-01"] * 10 + ["2015-01-01"] * 10 + ["2020-01-01"] * 10,
                     dtype="datetime64[D]")
    assert not np.array_equal(signal, time_shuffle(signal, years))
