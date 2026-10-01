"""## Executive summary (read this first)

Daily returns are innovations without another difference; levels differ once.
"""

import pandas as pd
import numpy as np
from qfbench2_track_forecasting.origin01.innovations import innovations, scaled


def test_asset_semantics_and_prior_scale():
    frame = pd.DataFrame({"level": np.arange(260.), "return": np.arange(260.) / 100})
    steps = innovations(frame, {"level": "level", "return": "log_return"})
    assert steps["return"].iloc[21] == frame["return"].iloc[21]
    assert steps["level"].iloc[21] == 1
    z, sigma = scaled(steps)
    assert pd.isna(sigma["return"].iloc[199])
    assert np.isfinite(sigma["return"].iloc[220])
