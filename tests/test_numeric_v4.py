"""## Executive summary (read this first)

Synthetic tests cover prefix causality, stress routing, exact F3 preservation,
frequency handling, tail monotonicity and whole-world distribution mixtures.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qfbench2_track_forecasting.numeric_v3 import forecast_numeric_v3
from qfbench2_track_forecasting.numeric_v4 import (
    V4_A,
    V4_AB,
    V4_B,
    calibrate_single_cell_tails,
    forecast_numeric_v4,
    lagged_volatility,
    mixture_draws,
    routing_weights,
    state_features,
    weighted_analogues,
)


def history(n: int = 500, monthly: bool = False) -> dict[str, pd.Series]:
    rng = np.random.default_rng(12)
    dates = (
        pd.date_range("1980-01-01", periods=n, freq="MS")
        if monthly
        else pd.bdate_range("2000-01-01", periods=n)
    ).astype(str)
    first = rng.normal(size=n)
    return {
        "SYN-A": pd.Series(first, index=dates),
        "SYN-B": pd.Series(0.8 * first + 0.2 * rng.normal(size=n), index=dates),
    }


def test_features_and_lagged_scale_never_read_future() -> None:
    frame = pd.DataFrame(history())
    changed = frame.copy()
    changed.iloc[300:] = 1e6
    pd.testing.assert_frame_equal(
        state_features(frame).iloc[:300], state_features(changed).iloc[:300]
    )
    # Even the first changed shock must not alter its OWN denominator.
    pd.testing.assert_frame_equal(
        lagged_volatility(frame).iloc[:301], lagged_volatility(changed).iloc[:301]
    )


def test_good_persistent_stress_keeps_analogues_but_bad_analogues_get_zero() -> None:
    low = routing_weights(0.1, 1.0, 1.0)
    high = routing_weights(1.0, 1.0, 1.0)
    assert high[1] > low[1] > 0
    assert routing_weights(1.0, 1.0, 0.0)[1] == 0
    np.testing.assert_allclose(high.sum(), 1)
    assert (high >= 0).all()
    with pytest.raises(ValueError):
        routing_weights(float("nan"), 1, 1)


def test_analogues_are_old_blocks_and_have_finite_probability_mass() -> None:
    starts, weights, quality = weighted_analogues(pd.DataFrame(history()), 5, 380)
    assert starts.size >= 20
    assert starts.min() >= 120 and starts.max() + 5 <= 380
    assert np.isfinite(weights).all() and (weights > 0).all()
    assert 0 <= quality <= 1
    np.testing.assert_allclose(weights.sum(), 1)


@pytest.mark.parametrize("config", [V4_A, V4_B, V4_AB])
def test_f3_is_frozen_in_every_numeric_candidate(config) -> None:
    h = history()
    args = (h, list(h), [5, 21], "log_return", "daily", 200, 1, "T2-F3")
    base = forecast_numeric_v3(*args)
    actual = forecast_numeric_v4(*args, config)
    np.testing.assert_array_equal(actual.samples, base.samples)
    assert actual.metadata == base.metadata


@pytest.mark.parametrize("config", [V4_A, V4_B, V4_AB])
@pytest.mark.parametrize("monthly", [False, True])
def test_candidates_are_finite_deterministic_and_frequency_aware(config, monthly) -> None:
    h = {"SYN-A": history(monthly=monthly)["SYN-A"].cumsum() + 100}
    args = (h, list(h), [21, 63], "level", "monthly" if monthly else "daily", 200, 17, "T2-F1")
    actual = forecast_numeric_v4(*args, config)
    repeated = forecast_numeric_v4(*args, config)
    assert actual.samples.shape == (200, 1, 2) and np.isfinite(actual.samples).all()
    np.testing.assert_array_equal(actual.samples, repeated.samples)
    assert actual.metadata["anchor"]["SYN-A"] == h["SYN-A"].iloc[-1]
    if monthly:
        assert actual.metadata["observation_horizons"][1] < 10


def test_tail_transform_preserves_center_order_and_multiple_cells() -> None:
    values = np.linspace(-5, 5, 1000).reshape(-1, 1, 1)
    transformed = calibrate_single_cell_tails(values, 1.15, 0.85)
    np.testing.assert_array_equal(transformed[100:900], values[100:900])
    assert (np.diff(transformed[:, 0, 0]) > 0).all()
    assert np.quantile(transformed, 0.05) < np.quantile(values, 0.05)
    assert np.quantile(transformed, 0.95) < np.quantile(values, 0.95)
    multi = np.repeat(values, 2, axis=2)
    np.testing.assert_array_equal(calibrate_single_cell_tails(multi, 1.15, 0.85), multi)
    np.testing.assert_array_equal(calibrate_single_cell_tails(values), values)
    with pytest.raises(ValueError):
        calibrate_single_cell_tails(values, -1, 1)


def test_mixture_uses_exact_allocation_and_whole_worlds() -> None:
    anchor = np.zeros((100, 2, 3))
    candidate = np.full_like(anchor, 10.0)
    result = mixture_draws(anchor, candidate, 0.30, 7)
    assert np.count_nonzero(result[:, 0, 0]) == 30
    assert np.all((result == 0).all(axis=(1, 2)) | (result == 10).all(axis=(1, 2)))


def test_short_history_returns_exact_baseline() -> None:
    h = history(n=50)
    args = (h, list(h), [5], "log_return", "daily", 200, 1, "T2-F1")
    np.testing.assert_array_equal(
        forecast_numeric_v4(*args, V4_AB).samples, forecast_numeric_v3(*args).samples
    )


def test_submission_default_remains_v3_and_experiments_require_numeric_mode(monkeypatch) -> None:
    from qfbench2_track_forecasting.cli import _draw

    h = history()
    panels = {
        "synthetic": pd.DataFrame(
            {
                "asset": ["SYN-A"] * len(h["SYN-A"]),
                "date": h["SYN-A"].index,
                "value": h["SYN-A"].values,
            }
        )
    }
    args = (panels, ["SYN-A"], [5], str(h["SYN-A"].index[-1]), 200, 17)
    monkeypatch.delenv("NUMERIC_VARIANT", raising=False)
    original = _draw(*args, target_type="log_return", family="T2-F4")[0]
    baseline = forecast_numeric_v3(
        {"SYN-A": h["SYN-A"]}, ["SYN-A"], [5], "log_return", "daily", 200, 17, "T2-F4"
    )
    np.testing.assert_array_equal(original, baseline.samples)
    monkeypatch.setenv("NUMERIC_VARIANT", "v4-a")
    monkeypatch.setenv("FORECAST_MODE", "f4-only")
    with pytest.raises(SystemExit, match="require FORECAST_MODE=numeric"):
        _draw(*args, target_type="log_return", family="T2-F4")
    monkeypatch.setenv("FORECAST_MODE", "numeric")
    candidate, stats = _draw(*args, target_type="log_return", family="T2-F4")
    assert stats["model"] == V4_A.name
    assert not np.array_equal(candidate, original)
