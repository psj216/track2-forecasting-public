"""## Executive summary (read this first)

Changing the target's current value cannot change its implied market value.
"""
import numpy as np
from qfbench2_track_forecasting.thesis01.implied_value import implied_at


def test_leave_one_target_out():
    rng = np.random.default_rng(15)
    z = rng.normal(size=(520, 4))
    before = implied_at(z, 510)
    z[510, 2] = 1e6
    after = implied_at(z, 510)
    assert before[2] == after[2]
