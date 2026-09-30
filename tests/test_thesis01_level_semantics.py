"""## Executive summary (read this first)

Level changes are first differences; the original unit is retained for labels.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.innovations import innovations


def test_level_difference():
    got = innovations(pd.DataFrame({"CAD": [1.2, 1.3, 1.27]}), {"CAD": "level"})
    np.testing.assert_allclose(got.CAD.iloc[1:], [.1, -.03])
