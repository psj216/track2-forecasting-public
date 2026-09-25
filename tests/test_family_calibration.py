"""## Executive summary (read this first)

Test future-prefix isolation, training-date gating, and preservation of F3 worlds.
These checks exercise the new head's causal and dependence contracts.
"""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from qfbench2_track_forecasting.family_calibration import (
    FamilyCalibration,
    apply_family_calibration,
    candidate_grid,
)


def inputs():
    series = pd.Series(np.linspace(1, 3, 300), index=pd.bdate_range("2000-01-01", periods=300))
    draws = np.random.default_rng(8).normal(4, 0.5, (200, 1, 2))
    return (
        draws,
        {"rate": series},
        ["rate"],
        [21, 126],
        "level",
        "T2-F1",
        str(series.index[199].date()),
    )


def test_future_prefix_and_rank_preservation():
    args = list(inputs())
    cfg = FamilyCalibration("test", "reversion", 0.25, 0.95, -0.1)
    result = apply_family_calibration(*args, cfg)
    args[1] = {"rate": args[1]["rate"].iloc[:200]}
    np.testing.assert_array_equal(result, apply_family_calibration(*args, cfg))
    np.testing.assert_array_equal(np.argsort(result, axis=0), np.argsort(args[0], axis=0))
    assert not np.array_equal(result, args[0])


def test_training_label_cannot_time_travel():
    args = inputs()
    cfg = FamilyCalibration("trained", scale=0.95, trained_through=args[-1])
    with pytest.raises(ValueError, match="training labels"):
        apply_family_calibration(*args, cfg)


def test_other_families_are_exact_bypass():
    args = list(inputs())
    for family in ("T2-F2", "T2-F3", "T2-F4"):
        args[5] = family
        for cfg in candidate_grid():
            np.testing.assert_array_equal(apply_family_calibration(*args, cfg), args[0])


def test_identity_and_width_without_center_change():
    args = inputs()
    np.testing.assert_array_equal(apply_family_calibration(*args, FamilyCalibration()), args[0])
    transformed = apply_family_calibration(*args, FamilyCalibration("scale", scale=0.85))
    np.testing.assert_allclose(transformed.mean(axis=0), args[0].mean(axis=0))
    np.testing.assert_allclose(transformed.std(axis=0), 0.85 * args[0].std(axis=0))


def test_persistence_is_halfway_between_anchor_and_v3_center():
    args = inputs()
    result = apply_family_calibration(*args, FamilyCalibration("persistence", "persistence", 0.5))
    anchor = args[1]["rate"].iloc[199]
    np.testing.assert_allclose(result.mean(axis=0), 0.5 * (args[0].mean(axis=0) + anchor))


def test_invalid_parameters_and_insufficient_history():
    args = list(inputs())
    with pytest.raises(ValueError, match="bounds"):
        apply_family_calibration(*args, FamilyCalibration("bad", scale=2))
    args[1] = {"rate": args[1]["rate"].iloc[:20]}
    np.testing.assert_array_equal(
        apply_family_calibration(*args, FamilyCalibration("scale", scale=0.85)), args[0]
    )


def test_identity_with_training_metadata_still_exact():
    args = inputs()
    # Identity is selected when no candidate passes; metadata must not perturb draws.
    config = replace(FamilyCalibration(), trained_through="1999-01-01")
    np.testing.assert_array_equal(apply_family_calibration(*args, config), args[0])


def test_nonlevel_targets_bypass():
    args = list(inputs())
    for target in ("pct_change", "log_return", "return"):
        args[4] = target
        np.testing.assert_array_equal(
            apply_family_calibration(*args, FamilyCalibration("scale", scale=0.85)), args[0]
        )


def test_loader_requires_training_provenance(tmp_path):
    from qfbench2_track_forecasting.family_calibration import load_family_calibration

    config = tmp_path / "config.json"
    config.write_text('{"name":"scale","scale":0.85}')
    with pytest.raises(ValueError, match="trained_through"):
        load_family_calibration(config)
    config.write_text('{"name":"scale","scale":0.85,"trained_through":"NaT"}')
    with pytest.raises(ValueError, match="invalid"):
        load_family_calibration(config)
