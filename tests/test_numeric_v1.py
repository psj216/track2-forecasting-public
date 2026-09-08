"""## Executive summary (read this first)

These tests pin the Phase 3 numeric engine's core contracts: target-aware anchoring, a hard as-of
cutoff upstream, and one coherent joint path across assets and horizons.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.cli import _draw
from qfbench2_track_forecasting.numeric_v1 import forecast_numeric_v1


def _dated(values: np.ndarray) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2020-01-01", periods=len(values)).astype(str))


def test_log_return_starts_at_zero_instead_of_last_daily_return() -> None:
    rng = np.random.default_rng(7)
    daily = rng.normal(0.0005, 0.01, 600)
    result = forecast_numeric_v1({"MKT": _dated(daily)}, ["MKT"], [21], "log_return", 500, seed=11)

    assert result.samples.shape == (500, 1, 1)
    assert result.metadata["anchor"]["MKT"] == 0.0
    assert abs(float(np.median(result.samples[:, 0, 0]))) < 0.15


def test_level_target_starts_from_latest_level() -> None:
    rng = np.random.default_rng(3)
    increments = rng.normal(0.0, 0.02, 600)
    levels = 4.0 + np.cumsum(increments)
    result = forecast_numeric_v1({"UST_2Y": _dated(levels)}, ["UST_2Y"], [21], "level", 500, seed=5)

    assert result.metadata["anchor"]["UST_2Y"] == levels[-1]
    assert abs(float(np.median(result.samples[:, 0, 0])) - levels[-1]) < 0.25


def test_joint_assets_and_horizons_share_one_world_path() -> None:
    rng = np.random.default_rng(19)
    first = rng.normal(0.0, 0.01, 700)
    second = 2.0 * first
    result = forecast_numeric_v1(
        {"A": _dated(first), "B": _dated(second)},
        ["A", "B"],
        [5, 21],
        "log_return",
        400,
        seed=23,
    )

    np.testing.assert_allclose(result.samples[:, 1, :], 2.0 * result.samples[:, 0, :])
    assert np.corrcoef(result.samples[:, 0, 0], result.samples[:, 0, 1])[0, 1] > 0.25


def test_fragility_reduces_recent_weight_and_increases_width() -> None:
    calm = np.tile(np.array([-0.001, 0.001]), 300)
    unstable = calm.copy()
    unstable[-20:] *= 12.0
    calm_result = forecast_numeric_v1(
        {"MKT": _dated(calm)}, ["MKT"], [21], "log_return", 300, seed=2
    )
    unstable_result = forecast_numeric_v1(
        {"MKT": _dated(unstable)}, ["MKT"], [21], "log_return", 300, seed=2
    )

    calm_regime = calm_result.metadata["regime"]
    unstable_regime = unstable_result.metadata["regime"]
    assert unstable_regime["fragility"] > calm_regime["fragility"]
    assert unstable_regime["recent_weight"] < calm_regime["recent_weight"]
    assert unstable_regime["uncertainty_scale"] > calm_regime["uncertainty_scale"]


def test_cli_draw_ignores_rows_after_asof() -> None:
    dates = pd.bdate_range("2020-01-01", periods=401).astype(str)
    values = np.linspace(1.0, 1.4, 401)
    panel = pd.DataFrame({"date": dates, "asset": "EUR", "value": values})
    cutoff = str(dates[399])[:10]

    with_future = _draw({"fx": panel}, ["EUR"], [21], cutoff, 300, seed=31, target_type="level")[0]
    without_future = _draw(
        {"fx": panel.iloc[:-1]}, ["EUR"], [21], cutoff, 300, seed=31, target_type="level"
    )[0]

    np.testing.assert_array_equal(with_future, without_future)
