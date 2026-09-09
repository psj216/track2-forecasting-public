"""## Executive summary (read this first)

These tests pin the Phase 3 numeric engine's core contracts: target-aware anchoring, a hard as-of
cutoff upstream, and one coherent joint path across assets and horizons.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.cli import _draw
from qfbench2_track_forecasting.numeric_v1 import forecast_numeric_v1
from qfbench2_track_forecasting.numeric_v2 import V2_CONFIG, forecast_numeric_v2
from qfbench2_track_forecasting.numeric_v21 import V21_CONFIG, forecast_numeric_v21


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


def test_v2_adds_state_matched_pool_without_changing_shape() -> None:
    rng = np.random.default_rng(41)
    daily = rng.normal(0.0, 0.01, 900)
    result = forecast_numeric_v2(
        {"MKT": _dated(daily)}, ["MKT"], [21, 63], "log_return", 300, seed=43
    )

    assert result.samples.shape == (300, 1, 2)
    assert result.metadata["model"] == V2_CONFIG.name
    sampling = result.metadata["sampling"]
    assert sampling["configured_state_match_share"] == 0.75
    assert 0.0 < sampling["effective_state_match_share"] < 0.75
    assert sampling["state_matched_block_count"] >= 20


def test_v21_maps_monthly_observations_to_business_day_horizons() -> None:
    rng = np.random.default_rng(47)
    monthly_steps = rng.normal(0.0, 1.0, 240)
    dates = pd.date_range("2000-01-01", periods=240, freq="MS").astype(str)
    levels = pd.Series(100.0 + np.cumsum(monthly_steps), index=dates)

    result = forecast_numeric_v21(
        {"CPI": levels}, ["CPI"], [21, 63], "level", "monthly", 400, seed=53
    )

    assert result.metadata["model"] == V21_CONFIG.name
    assert 20 <= result.metadata["observation_period_business_days"] <= 23
    assert result.metadata["observation_horizons"] == [1, 3]
    short = result.samples[:, 0, 0] - levels.iloc[-1]
    long = result.samples[:, 0, 1] - levels.iloc[-1]
    assert long.std(ddof=1) > short.std(ddof=1)


def test_v21_is_identical_to_v2_for_daily_panels() -> None:
    rng = np.random.default_rng(59)
    daily = rng.normal(0.0, 0.01, 900)
    history = {"MKT": _dated(daily)}

    v2 = forecast_numeric_v2(history, ["MKT"], [21, 63], "log_return", 300, seed=61)
    v21 = forecast_numeric_v21(history, ["MKT"], [21, 63], "log_return", "daily", 300, seed=61)

    np.testing.assert_array_equal(v21.samples, v2.samples)
