"""## Executive summary (read this first)

These tests pin the dynamic transmission layer's safety contracts. It must bypass single-asset
cards, preserve every marginal draw exactly, and move multi-asset dependence toward the estimated
current regime without creating non-finite samples.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.numeric_v1 import NumericForecast
from qfbench2_track_forecasting.numeric_v3 import TransmissionConfig, apply_dynamic_transmission


def _history(first: np.ndarray, second: np.ndarray) -> dict[str, pd.Series]:
    dates = pd.bdate_range("2010-01-01", periods=len(first)).astype(str)
    return {
        "A": pd.Series(first, index=dates),
        "B": pd.Series(second, index=dates),
    }


def _baseline(samples: np.ndarray) -> NumericForecast:
    return NumericForecast(samples=samples, metadata={"regime": {"fragility": 0.2}})


def test_single_asset_bypasses_transmission_exactly() -> None:
    rng = np.random.default_rng(5)
    samples = rng.normal(size=(300, 1, 2))
    history = {"A": pd.Series(rng.normal(size=400))}

    result = apply_dynamic_transmission(
        _baseline(samples),
        history,
        ["A"],
        "log_return",
        TransmissionConfig(name="test"),
        family="T2-F3",
    )

    np.testing.assert_array_equal(result.samples, samples)


def test_transmission_preserves_every_marginal_draw() -> None:
    rng = np.random.default_rng(7)
    samples = rng.normal(size=(500, 2, 2))
    first = rng.normal(size=500)
    history = _history(first, 0.8 * first + rng.normal(scale=0.2, size=500))

    result = apply_dynamic_transmission(
        _baseline(samples),
        history,
        ["A", "B"],
        "log_return",
        TransmissionConfig(name="test"),
        family="T2-F3",
    )

    for asset_index in range(2):
        for horizon_index in range(2):
            np.testing.assert_array_equal(
                np.sort(result.samples[:, asset_index, horizon_index]),
                np.sort(samples[:, asset_index, horizon_index]),
            )


def test_transmission_moves_dependence_toward_recent_regime() -> None:
    rng = np.random.default_rng(11)
    old_first = rng.normal(size=400)
    old_second = -old_first + rng.normal(scale=0.2, size=400)
    recent_first = rng.normal(size=120)
    recent_second = recent_first + rng.normal(scale=0.1, size=120)
    history = _history(
        np.concatenate([old_first, recent_first]),
        np.concatenate([old_second, recent_second]),
    )
    raw = rng.multivariate_normal([0.0, 0.0], [[1.0, -0.7], [-0.7, 1.0]], size=1000)
    samples = raw[:, :, None]
    config = TransmissionConfig(name="test", strength=0.75, identity_shrinkage=0.05)

    result = apply_dynamic_transmission(
        _baseline(samples), history, ["A", "B"], "log_return", config, family="T2-F3"
    )

    source = float(np.corrcoef(samples[:, :, 0], rowvar=False)[0, 1])
    output = float(np.corrcoef(result.samples[:, :, 0], rowvar=False)[0, 1])
    target = float(result.metadata["transmission"]["target_correlation"][0][1])
    assert abs(output - target) < abs(source - target)
    assert np.isfinite(result.samples).all()


def test_non_f3_family_bypasses_transmission_exactly() -> None:
    rng = np.random.default_rng(13)
    samples = rng.normal(size=(300, 2, 1))
    first = rng.normal(size=500)
    history = _history(first, first + rng.normal(scale=0.2, size=500))

    result = apply_dynamic_transmission(
        _baseline(samples),
        history,
        ["A", "B"],
        "log_return",
        TransmissionConfig(name="test"),
        family="T2-F4",
    )

    np.testing.assert_array_equal(result.samples, samples)
