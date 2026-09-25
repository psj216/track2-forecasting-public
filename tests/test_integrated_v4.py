"""## Executive summary (read this first)

Verify exact V3 fallback for F3 and uncertain F2, cutoff-safe text, and actual
historical stress-world activation only after persistent numeric stress.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.integrated_v4 import (
    CONFIGS,
    _explicit_direction,
    apply_integrated_v4,
)


def inputs(n: int = 450):
    dates = pd.bdate_range("2019-01-01", periods=n)
    rng = np.random.default_rng(13)
    steps = rng.normal(0, 0.01, n)
    series = pd.Series(3.0 + steps.cumsum(), index=dates)
    samples = np.linspace(2.5, 3.5, 500, dtype=float).reshape(500, 1, 1)
    return dates, series, samples


def test_f3_and_uncertain_f2_are_exact_numeric():
    dates, series, samples = inputs()
    for family in ("T2-F3", "T2-F2"):
        result, meta = apply_integrated_v4(
            samples,
            {"UST_2Y": series},
            ["UST_2Y"],
            [21],
            "level",
            "daily",
            family,
            str(dates[-1].date()),
            12,
            CONFIGS[0],
            None,
        )
        assert np.array_equal(result, samples)
        assert not meta["applied"]


def test_text_after_asof_never_activates(tmp_path: Path):
    (tmp_path / "late.txt").write_text("UST_2Y rises as policy changes.")
    (tmp_path / "corpus_index.json").write_text(
        json.dumps(
            {
                "documents": [
                    {"doc_id": "late", "file": "late.txt", "timestamp": "2020-03-01"},
                ]
            }
        )
    )
    assert _explicit_direction(tmp_path, "2020-02-01", "UST_2Y") == (0, (), "continuation")
    assert _explicit_direction(tmp_path, "2020-03-02", "UST_2Y") == (1, ("late",), "policy_shift")
    (tmp_path / "corpus_index.json").write_text("invalid JSON")
    assert _explicit_direction(tmp_path, "2020-03-02", "UST_2Y") == (0, (), "continuation")


def test_f2_grounded_numeric_agreement_reaches_historical_worlds(tmp_path: Path):
    rng = np.random.default_rng(3)
    dates = pd.bdate_range("2018-01-01", periods=800)
    moves = rng.normal(0, 0.015, len(dates))
    moves[-20:] += 0.012
    series = pd.Series(3 + moves.cumsum(), index=dates)
    samples = np.random.default_rng(4).normal(series.iloc[-1], 0.1, (500, 1, 1))
    (tmp_path / "event.txt").write_text("UST_2Y rises as the policy direction shifts.")
    (tmp_path / "corpus_index.json").write_text(
        json.dumps(
            {
                "documents": [
                    {"doc_id": "event", "file": "event.txt", "timestamp": str(dates[-1].date())},
                ]
            }
        )
    )
    result, meta = apply_integrated_v4(
        samples,
        {"UST_2Y": series},
        ["UST_2Y"],
        [21],
        "level",
        "daily",
        "T2-F2",
        str(dates[-1].date()),
        7,
        CONFIGS[1],
        tmp_path,
    )
    assert meta["applied"] and meta["evidence_count"] == 1
    assert not np.array_equal(samples, result)


def test_high_recent_volatility_does_not_shrink_stress_worlds():
    dates, series, samples = inputs()
    # Two consecutive disjoint windows of high volatility trigger persistent stress.
    rng = np.random.default_rng(8)
    series.iloc[-40:] = series.iloc[-41] + rng.normal(0, 0.07, 40).cumsum()
    result, meta = apply_integrated_v4(
        samples,
        {"UST_2Y": series},
        ["UST_2Y"],
        [21],
        "level",
        "daily",
        "T2-F4",
        str(dates[-1].date()),
        12,
        CONFIGS[2],
        None,
    )
    assert meta["reason"] == "stress_f4_worlds"
    assert meta["applied"]
    assert not np.array_equal(result, samples)
    assert np.std(result) >= np.std(samples)


def test_future_panel_values_cannot_change_same_asof_forecast():
    dates, series, samples = inputs()
    cutoff = str(dates[-41].date())
    before, _ = apply_integrated_v4(
        samples,
        {"UST_2Y": series},
        ["UST_2Y"],
        [21],
        "level",
        "daily",
        "T2-F4",
        cutoff,
        12,
        CONFIGS[1],
        None,
    )
    changed = series.copy()
    changed.iloc[-40:] += 1000
    after, _ = apply_integrated_v4(
        samples,
        {"UST_2Y": changed},
        ["UST_2Y"],
        [21],
        "level",
        "daily",
        "T2-F4",
        cutoff,
        12,
        CONFIGS[1],
        None,
    )
    assert np.array_equal(before, after)


def test_cli_f3_parquet_is_byte_identical_to_v3(tmp_path, monkeypatch):
    from qfbench2_track_forecasting import cli

    unit = Path(__file__).parents[1] / "units/t2-F3-brexit-joint-2016"
    args = [
        "--panels",
        str(unit / "panels"),
        "--text",
        str(unit / "text"),
        "--asof",
        "2016-06-23",
        "--seed",
        "19",
        "--n-draws",
        "500",
    ]
    monkeypatch.setenv("FORECAST_MODE", "numeric")
    base = tmp_path / "numeric/forecast.parquet"
    assert cli.main([*args, "--out", str(base)]) == 0
    monkeypatch.setenv("FORECAST_MODE", "integrated-v4")
    candidate = tmp_path / "v4/forecast.parquet"
    assert cli.main([*args, "--out", str(candidate)]) == 0
    assert base.read_bytes() == candidate.read_bytes()
