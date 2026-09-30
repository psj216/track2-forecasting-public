"""## Executive summary (read this first)

Daily factor returns are innovations, not differences of daily returns.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.innovations import innovations


def test_returns_are_not_differenced():
    panel = pd.DataFrame({"MKT": [.01, .02, -.03]})
    np.testing.assert_allclose(innovations(panel, {"MKT": "log_return"})["MKT"], panel["MKT"])
