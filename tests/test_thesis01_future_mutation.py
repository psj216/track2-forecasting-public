"""## Executive summary (read this first)

Mutating data after t cannot change t's scale or either implied value.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.scaling import scaled
from qfbench2_track_forecasting.thesis01.tension import at


def test_future_mutation_both_signals():
    rng = np.random.default_rng(12)
    steps = pd.DataFrame(rng.normal(size=(900, 4)))
    z, _ = scaled(steps)
    original = [at(z.to_numpy(), 760, lag=lag) for lag in (0, 1)]
    steps.iloc[761:] = 1e5
    changed, _ = scaled(steps)
    for lag, value in zip((0, 1), original):
        np.testing.assert_array_equal(at(changed.to_numpy(), 760, lag=lag), value)
