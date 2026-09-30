"""## Executive summary (read this first)

The origin t scale uses historical values through t-1 only.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.scaling import scaled


def test_scale_excludes_origin():
    series = pd.DataFrame({"x": np.arange(300, dtype=float) % 7 + 1})
    a, sigma = scaled(series)
    mutated = series.copy(); mutated.loc[270, "x"] = 100000.0
    b, other = scaled(mutated)
    assert sigma.loc[270, "x"] == other.loc[270, "x"]
    assert a.loc[269, "x"] == b.loc[269, "x"]
