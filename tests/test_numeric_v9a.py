"""## Executive summary (read this first)

Pin V9-A's only intended difference: historical block length. A 5-day-only
mixture must equal V5.1 samples, F3 stays byte-identical, and every asset in
one world shares its historical block start.
"""

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.numeric_v9a import (
    MultiScaleConfig,
    forecast_numeric_v9a,
    sample_multiscale_blocks,
)


def _histories():
    rng = np.random.default_rng(11)
    dates = pd.date_range("2018-01-01", periods=700, freq="B")
    increments = rng.normal(0, 0.05, len(dates))
    return {"A": pd.Series(4 + np.cumsum(increments), index=dates)}


def test_degenerate_five_day_mixture_is_exact_baseline():
    histories = _histories()
    args = (histories, ["A"], [21, 63], "level", "daily", 200, 71, "T2-F1")
    base = forecast_numeric_v3(*args)
    same = forecast_numeric_v9a(*args, mixture=MultiScaleConfig((5,), (1.0,)))
    np.testing.assert_array_equal(same.samples, base.samples)


def test_f3_is_exact_even_with_multiscale_enabled():
    histories = _histories()
    args = (histories, ["A"], [21, 63], "level", "daily", 200, 71, "T2-F3")
    base = forecast_numeric_v3(*args)
    candidate = forecast_numeric_v9a(*args)
    assert candidate.samples.tobytes() == base.samples.tobytes()
    assert candidate.metadata == base.metadata


def test_shared_block_start_preserves_identical_asset_steps():
    rng = np.random.default_rng(4)
    increments = rng.normal(size=300)
    steps = pd.DataFrame({"A": increments, "B": increments})
    paths, meta = sample_multiscale_blocks(
        steps, 200, 45, 0.55, 1.1, np.zeros(2), 13, 0.2
    )
    np.testing.assert_array_equal(paths[:, :, 0], paths[:, :, 1])
    assert set(meta["block_selection_counts"]) == {1, 5, 20}
