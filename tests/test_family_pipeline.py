"""## Executive summary (read this first)

Check specialist wiring, exact kill-switch/F3 fallback, and deployment-time
calibration dates. All text replies are synthetic; these are not House scores.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from qfbench2_track_forecasting import family_pipeline as pipeline


def invoke(family: str, tmp_path: Path, *, enabled: bool = True):
    samples = np.arange(500, dtype=float).reshape(500, 1, 1) / 100 + 10
    histories = {
        "X": pd.Series(np.arange(300) / 100 + 10, index=pd.bdate_range("2019-01-01", periods=300))
    }
    result = pipeline.run_family_heads(
        samples,
        histories,
        ["X"],
        [21],
        "level",
        "daily",
        family,
        "2021-01-01",
        0,
        tmp_path,
        enabled=enabled,
    )
    return samples, result


@pytest.mark.parametrize("family,enabled", [("T2-F3", True), ("T2-F4", False)])
def test_frozen_family_and_kill_switch_never_call_model(tmp_path, monkeypatch, family, enabled):
    def forbidden(**kwargs):
        pytest.fail("model must not be called")

    monkeypatch.setattr(pipeline, "interpret_regime", forbidden)
    original, (result, meta) = invoke(family, tmp_path, enabled=enabled)
    assert np.array_equal(original, result)
    assert meta["numeric_fallback_exact"]


def test_validated_route_reaches_worlds_and_changes_samples(tmp_path, monkeypatch):
    route = SimpleNamespace(
        gate_passed=True,
        decision=object(),
        metadata=lambda **kwargs: {"gate_passed": True, **kwargs},
    )
    monkeypatch.setattr(pipeline, "interpret_regime", lambda **kwargs: route)

    def head(samples, *args, **kwargs):
        assert kwargs["evidence_valid"] is True
        changed = samples.copy()
        changed[:10] += 0.5
        return changed, {"reason": "synthetic specialist", "sleeve_weight": 0.02}

    monkeypatch.setattr(pipeline, "apply_historical_head", head)
    original, (result, meta) = invoke("T2-F4", tmp_path)
    assert not np.array_equal(original, result)
    assert meta["samples_changed"] and meta["router"]["samples_changed"]


@pytest.mark.parametrize("date", [None, "2022-01-01"])
def test_undated_or_future_calibration_falls_back(tmp_path, monkeypatch, date):
    config = tmp_path / "config.json"
    config.write_text(json.dumps(dict(name="scale-95", scale=0.95, trained_through=date)))
    monkeypatch.setenv("F1_CALIBRATION_PATH", str(config))
    original, (result, meta) = invoke("T2-F1", tmp_path)
    assert np.array_equal(original, result)
    assert not meta["applied"]


def test_cli_family_heads_real_sampler_and_cutoff_corpus(tmp_path, monkeypatch):
    from qfbench2_track_forecasting import cli, regime_router

    def fake_house(prompt):
        request = json.loads(prompt)
        document_id = request["documents"][0]["doc_id"]
        return regime_router.ModelReply(
            raw=dict(
                regime="liquidity_stress",
                direction=-1,
                confidence=1.0,
                tail_side="lower",
                horizon="short",
                evidence=[document_id],
            ),
            endpoint_configured=True,
            call_attempted=True,
            call_succeeded=True,
            parse_succeeded=True,
            model_name="synthetic-only",
        )

    monkeypatch.setattr(regime_router, "call_regime_model", fake_house)
    root = Path(__file__).parents[1]
    unit = root / "units/t2-F4-short-vol-2018"
    common = [
        "--panels",
        str(unit / "panels"),
        "--text",
        str(unit / "text"),
        "--asof",
        "2018-01-26",
        "--seed",
        "29",
    ]
    monkeypatch.setenv("FORECAST_MODE", "numeric")
    baseline = tmp_path / "base/forecast.parquet"
    assert cli.main([*common, "--out", str(baseline)]) == 0
    monkeypatch.setenv("FORECAST_MODE", "family-heads")
    candidate = tmp_path / "head/forecast.parquet"
    assert cli.main([*common, "--out", str(candidate)]) == 0
    meta = json.loads((candidate.parent / "forecast_meta.json").read_text())
    assert meta["family_heads"]["router"]["validation_succeeded"]
    assert meta["family_heads"]["router"]["samples_changed"]
    assert meta["forecast_adjustment_applied"]
    assert not pd.read_parquet(candidate).equals(pd.read_parquet(baseline))
    monkeypatch.setenv("TEXT_INTEGRATION", "off")
    killed = tmp_path / "killed/forecast.parquet"
    assert cli.main([*common, "--out", str(killed)]) == 0
    pd.testing.assert_frame_equal(
        pd.read_parquet(baseline), pd.read_parquet(killed), check_exact=True
    )
