"""## Executive summary (read this first)

This end-to-end test proves that the canonical `forecast` command integrates validated evidence
when enabled, records the transformation in both sidecars, and returns exactly to Numeric v3 when
the kill switch is off.  It uses a synthetic model result and no network call.
"""

from __future__ import annotations

import json
import pathlib

import pandas as pd
import pytest

import qfbench2_track_forecasting.cli as forecast_cli
from qfbench2_track_forecasting.scenario_integration import APPROVED_F4_CONFIG
from qfbench2_track_forecasting.text_evidence import SCENARIOS, CorpusResult, ReasoningResult


def _reasoning() -> ReasoningResult:
    evidence = {
        "market_state": {"label": "LIQUIDITY_STRESS", "confidence": 0.9, "doc_ids": ["d1"]},
        "evidence": [
            {
                "id": "E1",
                "doc_ids": ["d1"],
                "claim": "Crowded positioning raises unwind risk.",
                "shock": "LIQUIDITY",
                "stance": "support",
                "strength": 0.95,
                "confidence": 0.95,
                "relevance": 0.95,
                "asset_impacts": [{"asset": "MKT", "direction": "down", "intensity": 1.0}],
                "volatility_impact": "up",
                "tail_impact": "downside",
            },
            {
                "id": "E2",
                "doc_ids": ["d2"],
                "claim": "Calm conditions can persist.",
                "shock": "RISK",
                "stance": "support",
                "strength": 0.55,
                "confidence": 0.65,
                "relevance": 0.60,
                "asset_impacts": [{"asset": "MKT", "direction": "up", "intensity": 0.5}],
                "volatility_impact": "down",
                "tail_impact": "upside",
            },
        ],
        "views": {
            "long": {"thesis": "Calm persists.", "evidence_ids": ["E2"], "confidence": 0.5},
            "short": {"thesis": "Crowding unwinds.", "evidence_ids": ["E1"], "confidence": 0.9},
            "outlier": {
                "thesis": "Liquidity gaps lower.",
                "evidence_ids": ["E1"],
                "confidence": 0.7,
            },
        },
        "skeptic": {
            "common_assumption": "Liquidity remains available.",
            "challenge": "Dealer balance sheets may not absorb forced selling.",
            "evidence_ids": ["E1"],
        },
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
                "support": 0.55,
                "contradiction": 0.20,
                "confidence": 0.65,
                "relevance": 0.60,
                "evidence_ids": ["E2"],
            },
        ],
    }
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


@pytest.mark.parametrize("forecast_mode", ["full", "f4-only"])
def test_cli_applies_evidence_and_kill_switch_restores_v3(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, forecast_mode: str
) -> None:
    root = pathlib.Path(__file__).parents[1]
    unit = root / "units/t2-F4-short-vol-2018"
    monkeypatch.setattr(forecast_cli, "interpret_text_evidence", lambda **kwargs: _reasoning())
    monkeypatch.setenv("FORECAST_MODE", forecast_mode)

    integrated = tmp_path / "integrated/forecast.parquet"
    fallback = tmp_path / "fallback/forecast.parquet"
    common = [
        "--panels",
        str(unit / "panels"),
        "--text",
        str(unit / "text"),
        "--asof",
        "2018-01-26",
        "--n-draws",
        "500",
        "--seed",
        "29",
    ]

    monkeypatch.setenv("TEXT_INTEGRATION", "on")
    assert forecast_cli.main([*common, "--out", str(integrated)]) == 0
    monkeypatch.setenv("TEXT_INTEGRATION", "off")
    assert forecast_cli.main([*common, "--out", str(fallback)]) == 0

    integrated_frame = pd.read_parquet(integrated)
    fallback_frame = pd.read_parquet(fallback)
    assert not integrated_frame.equals(fallback_frame)
    integrated_meta = json.loads((integrated.parent / "forecast_meta.json").read_text())
    fallback_meta = json.loads((fallback.parent / "forecast_meta.json").read_text())
    assert integrated_meta["forecast_adjustment_applied"] is True
    assert integrated_meta["rationale"]["text_evidence"]["mode"] == "integrated"
    expected_shocks = int(round(APPROVED_F4_CONFIG.tail_fraction * 500))
    assert integrated_meta["rationale"]["scenario_integration"]["shock_draw_count"] == expected_shocks
    assert fallback_meta["forecast_adjustment_applied"] is False
    assert fallback_meta["rationale"]["scenario_integration"]["numeric_fallback_exact"] is True


def test_numeric_mode_never_reads_text_or_calls_the_model(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = pathlib.Path(__file__).parents[1]
    unit = root / "units/t2-F4-short-vol-2018"

    def forbidden_interpreter(**kwargs: object) -> ReasoningResult:
        raise AssertionError(f"numeric control called the evidence interpreter: {kwargs}")

    monkeypatch.setattr(forecast_cli, "interpret_text_evidence", forbidden_interpreter)
    monkeypatch.setenv("FORECAST_MODE", "numeric")
    output = tmp_path / "numeric/forecast.parquet"

    assert (
        forecast_cli.main(
            [
                "--panels",
                str(unit / "panels"),
                "--text",
                str(unit / "text"),
                "--asof",
                "2018-01-26",
                "--n-draws",
                "500",
                "--seed",
                "29",
                "--out",
                str(output),
            ]
        )
        == 0
    )

    meta = json.loads((output.parent / "forecast_meta.json").read_text())
    assert meta["forecast_mode"] == "numeric"
    assert meta["reasoning_applied"] is False
    assert meta["forecast_adjustment_applied"] is False
    assert meta["reasoning_skipped_reason"] == (
        "FORECAST_MODE=numeric disables reasoning for T2-F4"
    )


def test_f4_only_mode_bypasses_the_endpoint_on_other_families(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = pathlib.Path(__file__).parents[1]
    unit = root / "units/t2-F1-greater-confidence-2024"

    def forbidden_interpreter(**kwargs: object) -> ReasoningResult:
        raise AssertionError(f"F4-only control called the model on F1: {kwargs}")

    monkeypatch.setattr(forecast_cli, "interpret_text_evidence", forbidden_interpreter)
    monkeypatch.setenv("FORECAST_MODE", "f4-only")
    output = tmp_path / "f4-only/forecast.parquet"

    assert (
        forecast_cli.main(
            [
                "--panels",
                str(unit / "panels"),
                "--text",
                str(unit / "text"),
                "--asof",
                "2024-01-31",
                "--n-draws",
                "500",
                "--seed",
                "29",
                "--out",
                str(output),
            ]
        )
        == 0
    )

    meta = json.loads((output.parent / "forecast_meta.json").read_text())
    assert meta["forecast_mode"] == "f4-only"
    assert meta["reasoning_applied"] is False
    assert meta["reasoning_skipped_reason"] == (
        "FORECAST_MODE=f4-only disables reasoning for T2-F1"
    )


def test_invalid_forecast_mode_fails_before_model_use(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORECAST_MODE", "maybe")

    with pytest.raises(SystemExit, match="FORECAST_MODE must be one of"):
        forecast_cli._forecast_mode()
