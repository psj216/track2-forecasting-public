"""## Executive summary (read this first)

Synthetic worlds verify cutoff isolation, exact baseline gates, actual historical
trajectory reuse, joint coherence, monthly observations and sparse-tail refusal.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from qfbench2_track_forecasting.historical_heads import apply_historical_head
from qfbench2_track_forecasting.regime_router import RegimeDecision


def _history(monthly: bool = False) -> dict[str, pd.Series]:
    dates = pd.date_range("1980-01-01", periods=600, freq="MS" if monthly else "B")
    moves = np.random.default_rng(81).normal(0, 0.02, len(dates))
    return {"A": pd.Series(moves, index=dates), "B": pd.Series(2 * moves, index=dates)}


def _decision() -> RegimeDecision:
    return RegimeDecision("policy_shift", 1, 1.0, "upper", "short", ("doc-1",))


def _apply(history=None, samples=None, family="T2-F2", decision=None, **kwargs):
    history = history if history is not None else {"A": _history()["A"]}
    samples = samples if samples is not None else np.full((200, len(history), 2), -999.0)
    return apply_historical_head(
        samples,
        history,
        list(history),
        kwargs.pop("horizons", [1, 5]),
        kwargs.pop("target_type", "log_return"),
        kwargs.pop("target_frequency", "daily"),
        family,
        kwargs.pop("asof", str(history["A"].index[-1].date())),
        12,
        decision if decision is not None else _decision(),
        **kwargs,
    )


@pytest.mark.parametrize("family", ["T2-F1", "T2-F3"])
def test_frozen_families_bypass_exactly(family):
    samples = np.arange(400.0).reshape(200, 1, 2)
    result, meta = _apply(samples=samples, family=family, evidence_valid=True)
    np.testing.assert_array_equal(result, samples)
    assert not meta["applied"]


@pytest.mark.parametrize(
    "decision,evidence_valid",
    [
        (_decision(), False),
        (replace(_decision(), confidence=0.64), True),
        (replace(_decision(), evidence=()), True),
        (replace(_decision(), regime="continuation"), True),
        (replace(_decision(), confidence=float("nan")), True),
    ],
)
def test_untrusted_or_weak_text_leaves_anchor_exact(decision, evidence_valid):
    result, meta = _apply(decision=decision, evidence_valid=evidence_valid)
    np.testing.assert_array_equal(result, -999.0)
    assert not meta["applied"]


def test_future_rows_cannot_change_worlds_or_anchor():
    history = {"A": _history()["A"].cumsum() + 100}
    cutoff = str(history["A"].index[449].date())
    prefix = {"A": history["A"].iloc[:450]}
    poisoned = {"A": history["A"].copy()}
    poisoned["A"].iloc[450:] = 1e15
    first, meta = _apply(prefix, asof=cutoff, target_type="level", evidence_valid=True)
    second, later_meta = _apply(poisoned, asof=cutoff, target_type="level", evidence_valid=True)
    assert meta["applied"]
    np.testing.assert_array_equal(first, second)
    assert meta == later_meta


@pytest.mark.parametrize("family,draws", [("T2-F2", 30), ("T2-F4", 20)])
def test_replacements_are_actual_joint_historical_paths(family, draws):
    history = _history()
    result, meta = _apply(history, family=family, evidence_valid=True, direction_asset="A")
    assert meta["replacement_draws"] == draws
    changed = (result != -999).any(axis=(1, 2))
    assert changed.sum() == draws
    np.testing.assert_allclose(result[changed, 1], 2 * result[changed, 0])
    original = history["A"].to_numpy()
    permitted = np.array([[original[i], original[i : i + 5].sum()] for i in range(596)])
    for world in result[changed, 0]:
        assert np.any(np.all(np.isclose(permitted, world), axis=1))
        assert world[0] > 0
    np.testing.assert_array_equal(result[~changed], -999.0)


def test_multiasset_direction_requires_explicit_reference():
    result, meta = _apply(_history(), evidence_valid=True)
    assert meta["reason"] == "ambiguous_direction_asset"
    np.testing.assert_array_equal(result, -999.0)


def test_monthly_horizons_use_observations_and_level_anchor():
    history = {"A": _history(monthly=True)["A"].cumsum() + 100}
    result, meta = _apply(
        history,
        horizons=[21, 63],
        target_frequency="monthly",
        target_type="level",
        evidence_valid=True,
    )
    assert meta["applied"] and max(meta["observation_horizons"]) < 5
    assert np.all(result[result != -999] > 95)
    steps = history["A"].diff().dropna().to_numpy()
    hs = meta["observation_horizons"]
    possible = np.array(
        [[steps[i : i + h].sum() for h in hs] for i in range(len(steps) - max(hs) + 1)]
    )
    for world in result[result[:, 0, 0] != -999, 0]:
        residual = world - history["A"].iloc[-1]
        assert np.any(np.all(np.isclose(possible, residual), axis=1))


def test_sparse_stress_does_not_replicate_one_episode():
    history = {"A": _history()["A"] * 0}
    history["A"].iloc[20] = 1
    result, meta = _apply(history, family="T2-F4", evidence_valid=True)
    assert meta["reason"] == "sparse_historical_support"
    np.testing.assert_array_equal(result, -999.0)


def test_missing_rows_are_not_glued_into_false_worlds():
    history = {"A": _history()["A"].copy()}
    history["A"].iloc[::3] = np.nan
    result, meta = _apply(history, evidence_valid=True)
    assert meta["reason"] == "insufficient_contiguous_worlds"
    np.testing.assert_array_equal(result, -999.0)


def test_simple_returns_are_explicitly_bypassed():
    result, meta = _apply(target_type="simple_return", evidence_valid=True)
    assert meta["reason"] == "unsupported_target_type"
    np.testing.assert_array_equal(result, -999.0)


@pytest.mark.parametrize("side", ["lower", "both"])
def test_stress_side_is_explicit_and_bounded(side):
    decision = replace(_decision(), tail_side=side, direction=0, confidence=0.825)
    result, meta = _apply(family="T2-F4", decision=decision, evidence_valid=True)
    assert meta["applied"] and meta["replacement_draws"] == 10
    changed = result[:, 0, 0] != -999
    if side == "lower":
        assert np.all(result[changed, 0, 0] < 0)
    repeated, _ = _apply(family="T2-F4", decision=decision, evidence_valid=True)
    np.testing.assert_array_equal(result, repeated)


def test_calendar_gaps_cannot_be_crossed_by_historical_trajectory():
    # Two-observation islands, separated by months: no actual five-step path.
    history = {"A": _history()["A"].iloc[:200].copy()}
    dates = []
    for date in pd.date_range("1980-01-01", periods=100, freq="MS"):
        dates.extend([date, date + pd.Timedelta(days=1)])
    history["A"].index = pd.DatetimeIndex(dates)
    result, meta = _apply(history, evidence_valid=True)
    assert meta["reason"] == "insufficient_contiguous_worlds"
    np.testing.assert_array_equal(result, -999.0)


def test_copy_on_write_history_can_build_worlds():
    with pd.option_context("mode.copy_on_write", True):
        _, meta = _apply(evidence_valid=True)
    assert meta["applied"]
