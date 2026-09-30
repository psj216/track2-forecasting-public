"""## Executive summary (read this first)

Changing one level's currency units leaves its standardized signal unchanged.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.innovations import innovations
from qfbench2_track_forecasting.thesis01.scaling import scaled


def test_unit_rescaling():
    rng = np.random.default_rng(3)
    levels = pd.DataFrame({"FX": np.cumsum(rng.normal(size=550))})
    a, _ = scaled(innovations(levels, {"FX": "level"}))
    b, _ = scaled(innovations(levels * 100, {"FX": "level"}))
    np.testing.assert_allclose(a["FX"], b["FX"], equal_nan=True, atol=1e-11)
