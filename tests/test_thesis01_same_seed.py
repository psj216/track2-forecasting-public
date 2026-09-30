"""## Executive summary (read this first)

V5.1 no-text prior preserves deterministic draws for a frozen origin and seed.
"""
import numpy as np
import pandas as pd
from qfbench2_track_forecasting.thesis01.v51_shift import v51_no_text_prior


def test_v51_repeated_seed():
    rng = np.random.default_rng(2)
    s = pd.Series(np.cumsum(rng.normal(size=700)), index=pd.bdate_range("2000-01-03", periods=700))
    kw = dict(series=s, asset="CAD", kind="level", horizons=[5, 21], family="T2-F2",
              asof=str(s.index[-1].date()), seed=19, n_draws=500)
    np.testing.assert_array_equal(v51_no_text_prior(**kw), v51_no_text_prior(**kw))
