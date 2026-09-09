"""## Executive summary (read this first)

These tests pin Phase 5's distribution contracts.  Missing evidence and the kill switch must keep
Numeric v3 exact.  F3 may change only joint pairing.  F4 must create a bounded directional tail.
Every route must be deterministic and use one sampled scenario count per complete draw.
"""

from __future__ import annotations

import numpy as np

from qfbench2_track_forecasting.scenario_integration import integrate_scenario_worlds
from qfbench2_track_forecasting.text_evidence import (
    SCENARIOS,
    CorpusResult,
    ReasoningResult,
    scenario_probability_ledger,
)


def _evidence() -> dict[str, object]:
    return {
        "market_state": {"label": "LIQUIDITY_STRESS", "confidence": 0.9, "doc_ids": ["d1"]},
        "evidence": [
            {
                "id": "E1",
                "doc_ids": ["d1"],
                "claim": "Funding stress is rising.",
                "shock": "LIQUIDITY",
                "stance": "support",
                "strength": 0.95,
                "confidence": 0.95,
                "relevance": 0.95,
                "asset_impacts": [
                    {"asset": "A", "direction": "down", "intensity": 1.0},
                    {"asset": "B", "direction": "up", "intensity": 0.8},
                ],
                "volatility_impact": "up",
                "tail_impact": "downside",
            },
            {
                "id": "E2",
                "doc_ids": ["d2"],
                "claim": "A policy response remains possible.",
                "shock": "POLICY",
                "stance": "support",
                "strength": 0.60,
                "confidence": 0.75,
                "relevance": 0.70,
                "asset_impacts": [
                    {"asset": "A", "direction": "up", "intensity": 0.7},
                    {"asset": "B", "direction": "down", "intensity": 0.5},
                ],
                "volatility_impact": "mixed",
                "tail_impact": "upside",
            },
        ],
        "views": {},
        "skeptic": {},
        "scenarios": [
            {
                "name": "LIQUIDITY_SHOCK",
                "support": 0.95,
                "contradiction": 0.05,
                "confidence": 0.95,
                "relevance": 0.95,
                "evidence_ids": ["E1"],
            },
            {
                "name": "SOFT_LANDING",
                "support": 0.60,
                "contradiction": 0.15,
                "confidence": 0.70,
                "relevance": 0.65,
                "evidence_ids": ["E2"],
            },
        ],
    }


def _reasoning(family: str = "T2-F4") -> ReasoningResult:
    evidence = _evidence()
    del family  # The fixture supplies explicit Python-side probabilities below.
    # Concentrate the synthetic fixture on the two explicitly modelled worlds.  These weights are
    # Python-side test inputs, not a model response.
    probabilities = {name: 0.01 for name in SCENARIOS}
    probabilities["LIQUIDITY_SHOCK"] = 0.72
    probabilities["SOFT_LANDING"] = 0.20
    return ReasoningResult(
        applied=True,
        skipped_reason="",
        evidence=evidence,
        scenario_probabilities=probabilities,
        corpus=CorpusResult((), 2, 0, 0, 0, 0),
        model_name="synthetic-test-model",
    )


def _samples(seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    first = rng.normal(size=(1000, 2))
    second = first + rng.normal(scale=0.7, size=(1000, 2))
    return np.stack([first, second], axis=2)


def test_missing_evidence_keeps_numeric_v3_exact() -> None:
    samples = _samples()
    reasoning = ReasoningResult(
        applied=False,
        skipped_reason="endpoint unavailable",
        evidence=None,
        scenario_probabilities=scenario_probability_ledger(None, "T2-F2"),
        corpus=CorpusResult((), 0, 0, 0, 0, 0),
        model_name="",
    )

    result = integrate_scenario_worlds(samples, reasoning, ["A", "B"], [21, 63], "T2-F2", 7)

    np.testing.assert_array_equal(result.samples, samples)
    assert result.metadata["numeric_fallback_exact"] is True


def test_kill_switch_keeps_numeric_v3_exact() -> None:
    samples = _samples()

    result = integrate_scenario_worlds(
        samples, _reasoning(), ["A", "B"], [21, 63], "T2-F4", 7, enabled=False
    )

    np.testing.assert_array_equal(result.samples, samples)
    assert "kill switch" in result.metadata["reason"]


def test_f3_changes_pairing_but_preserves_every_marginal_exactly() -> None:
    samples = _samples()
    result = integrate_scenario_worlds(
        samples, _reasoning("T2-F3"), ["A", "B"], [21, 63], "T2-F3", 11
    )

    assert not np.array_equal(result.samples, samples)
    assert result.metadata["marginals_preserved_exactly"] is True
    for asset_index in range(2):
        for horizon_index in range(2):
            np.testing.assert_array_equal(
                np.sort(result.samples[:, asset_index, horizon_index]),
                np.sort(samples[:, asset_index, horizon_index]),
            )


def test_f4_adds_a_bounded_directional_left_tail() -> None:
    samples = _samples()
    result = integrate_scenario_worlds(
        samples, _reasoning("T2-F4"), ["A", "B"], [21, 63], "T2-F4", 13
    )

    assert np.quantile(result.samples[:, 0, 1], 0.01) < np.quantile(samples[:, 0, 1], 0.01)
    scale = np.std(samples, axis=0, ddof=1)
    standardized_change = np.abs(result.samples - samples) / scale[None, :, :]
    assert float(np.max(standardized_change)) <= 3.5 + 1e-12
    assert result.metadata["shock_draw_count"] == 70


def test_f1_context_adjustment_stays_inside_small_cap() -> None:
    samples = _samples()
    result = integrate_scenario_worlds(
        samples, _reasoning("T2-F1"), ["A", "B"], [21, 63], "T2-F1", 17
    )

    scale = np.std(samples, axis=0, ddof=1)
    standardized_change = np.abs(result.samples - samples) / scale[None, :, :]
    assert float(np.max(standardized_change)) <= 0.15 + 1e-12
    assert result.metadata["shock_draw_count"] == 0


def test_world_sampling_is_deterministic_and_counts_one_world_per_draw() -> None:
    samples = _samples()
    first = integrate_scenario_worlds(
        samples, _reasoning("T2-F2"), ["A", "B"], [21, 63], "T2-F2", 23
    )
    second = integrate_scenario_worlds(
        samples, _reasoning("T2-F2"), ["A", "B"], [21, 63], "T2-F2", 23
    )

    np.testing.assert_array_equal(first.samples, second.samples)
    assert first.metadata == second.metadata
    assert sum(first.metadata["scenario_draw_counts"].values()) == samples.shape[0]
