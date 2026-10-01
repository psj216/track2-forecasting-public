"""## Executive summary (read this first)

Require 24 strictly prior errors and use the fixed clip.
"""

import numpy as np
from qfbench2_track_forecasting.surprise01.surprise import standardized


def test_prior_scale():
    assert standardized(99, np.arange(23)) is None
    assert standardized(99, np.arange(24)) == 5
    assert standardized(-99, np.arange(24)) == -5
    assert standardized(1, np.zeros(30)) is None
