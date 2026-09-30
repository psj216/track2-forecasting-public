"""Data parity contracts: cumulative factor features and cell-local maturity."""

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.v12.data_parity import _label
from qfbench2_track_forecasting.v12.joint_dataset import JointDataset
from qfbench2_track_forecasting.v12.joint_features import features, local_features


def test_factor_momentum_uses_cumulative_increments():
    rng = np.random.default_rng(9)
    increments = rng.normal(.002, .01, 160)
    scale = np.std(increments[-120:])
    actual = local_features(increments, "log_return")
    assert np.isclose(actual[2], increments[-20:].sum() / (scale * np.sqrt(20)))
    assert not np.isclose(actual[2], local_features(increments, "level")[2])
    # Volatility must use the daily increments rather than differences of returns.
    assert np.isclose(actual[10], np.std(increments[-20:]) / scale)


def test_return_feature_cutoff_and_global_factor_semantics():
    days = pd.bdate_range("2001-01-02", periods=180)
    daily = np.sin(np.arange(len(days)) / 12) * .01 + .001
    panel = pd.DataFrame({"date": days, "asset": "MKT", "value": daily})
    asof = str(days[150].date())
    x, g, available = features(panel, ["MKT"], asof, {"MKT": "log_return"})
    expected = daily[:151][-20:].sum() / (np.std(daily[:151][-120:]) * np.sqrt(20))
    assert available[0] and np.isclose(x[0, 2], expected)
    assert np.isclose(g[14], x[0, 2])
    altered = panel.copy()
    altered.loc[altered.date > asof, "value"] = 1000
    xx, gg, aa = features(altered, ["MKT"], asof, {"MKT": "log_return"})
    np.testing.assert_array_equal(x, xx)
    np.testing.assert_array_equal(g, gg)
    np.testing.assert_array_equal(available, aa)


def test_business_horizon_target_end_and_first_target_exclusion():
    dates = pd.bdate_range("2001-01-02", periods=120)
    values = pd.Series(np.full(len(dates), .01), index=dates)
    label = _label(values, "log_return", dates[0], 5, "2002-01-01", True)
    assert label is not None and label[1] == dates[5]
    assert np.isclose(label[0], .05)
    assert _label(values, "log_return", dates[0], 5,
                  str(dates[5].date()), True) is None


def test_fit_mask_uses_each_asset_actual_end():
    ends = np.array([[['2008-12-31', '2009-01-01']]], dtype="datetime64[ns]")
    data = JointDataset(['2008-12-01'], ['A', 'B'], np.zeros((1, 2, 19)),
                        np.zeros((1, 21)), np.zeros((1, 1, 2)),
                        np.ones((1, 1, 2), dtype=bool), ends)
    np.testing.assert_array_equal(data.fit_mask('2008-12-31'), [[[True, False]]])
