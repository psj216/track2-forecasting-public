"""## Executive summary (read this first)

Verify V8-A's bounded affine transform and exact frozen-family preservation.
"""

import numpy as np
import pytest

from backtesting.v8a_ablation import _gate
from qfbench2_track_forecasting.calibration_v8 import V8AConfig, transform_v8a


def test_frozen_families_and_identity_return_same_bytes():
    samples = np.arange(2400.0).reshape(200, 3, 4)
    config = V8AConfig(-0.05, 1.10, 0.05, 0.95)
    for family in ("T2-F3", "T2-F4"):
        result = transform_v8a(samples, family, config)
        assert result is samples and result.tobytes() == samples.tobytes()
    assert transform_v8a(samples, "T2-F1", V8AConfig()) is samples


def test_affine_calibration_changes_only_requested_family():
    rng = np.random.default_rng(7)
    samples = rng.normal(size=(500, 2, 3))
    original = samples.copy()
    config = V8AConfig(-0.05, 1.10, 0.05, 0.95)
    result = transform_v8a(samples, "T2-F1", config)
    median = np.median(samples, axis=0)
    q25, q75 = np.quantile(samples, (0.25, 0.75), axis=0)
    np.testing.assert_allclose(result, median - 0.05 * (q75 - q25) / 1.349
                               + 1.10 * (samples - median))
    np.testing.assert_array_equal(samples, original)
    assert not np.array_equal(result, samples)
    with pytest.raises(ValueError):
        transform_v8a(samples, "T2-F1", V8AConfig(f1_scale=1.11))


def test_submission_gate_requires_every_seed_and_chronological_block():
    def block(ratio):
        return {"all": {"geometric_ratio": ratio, "cases": 100,
                        "by_family": {"T2-F1": ratio, "T2-F2": ratio}}}

    strong = {"500:a": {"select": block(0.96), "holdout": block(0.96)}}
    assert _gate(strong)["pass"]
    strong["1000:b"] = {"select": block(0.96), "holdout": block(1.001)}
    assert not _gate(strong)["pass"]
    assert not _gate({"500:a": {"select": block(0.99), "holdout": block(0.99)}})["pass"]
