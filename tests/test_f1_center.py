"""## Executive summary (read this first)

Verify that the isolated F1 center route changes only F1 samples. F2/F3/F4
forecasts must be byte-identical to Numeric V3 without calling House.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from qfbench2_track_forecasting import cli
from qfbench2_track_forecasting.f1_center import CenterBias, apply_center_bias


def test_only_center_changes_and_cutoff_fails_closed():
    source = np.linspace(2, 3, 500).reshape(500, 1, 1)
    model = CenterBias("2013-12-31", 0.25, 0.1, {"daily:short": 0.5})
    changed = apply_center_bias(source, [21], "daily", "level", "T2-F1", "2024-01-01", model)
    assert not np.array_equal(changed, source)
    assert np.allclose(changed - changed.mean(axis=0), source - source.mean(axis=0), atol=1e-14)
    assert np.array_equal(
        apply_center_bias(source, [21], "daily", "level", "T2-F1", "2013-12-31", model), source
    )
    assert np.array_equal(
        apply_center_bias(source, [21], "daily", "level", "T2-F4", "2024-01-01", model), source
    )


@pytest.mark.parametrize(
    "unit_name",
    [
        "t2-F1-greater-confidence-2024",
        "t2-F2-cut-sizing-2024",
        "t2-F3-brexit-joint-2016",
        "t2-F4-short-vol-2018",
    ],
)
def test_cli_output_matches_numeric_except_f1(tmp_path, monkeypatch, unit_name):
    unit = Path(__file__).parents[1] / "units" / unit_name
    card = tomllib.loads((unit / "card.toml").read_text())
    asof = card["provenance"]["data_cutoff"]
    config = tmp_path / "f1-center.json"
    config.write_text(
        json.dumps(
            {
                "trained_through": "2013-12-31",
                "strength": 0.25,
                "cap": 0.1,
                "biases": {"daily:long": 0.5, "daily:medium": 0.5, "daily:short": 0.5},
            }
        )
    )
    monkeypatch.setenv("F1_CENTER_PATH", str(config))
    monkeypatch.setenv("NUMERIC_VARIANT", "v3")
    monkeypatch.setenv("TEXT_INTEGRATION", "off")
    args = [
        "--panels",
        str(unit / "panels"),
        "--text",
        str(unit / "text"),
        "--asof",
        asof,
        "--seed",
        "29",
        "--n-draws",
        "500",
    ]
    monkeypatch.setenv("FORECAST_MODE", "numeric")
    base = tmp_path / "base" / "forecast.parquet"
    assert cli.main([*args, "--out", str(base)]) == 0
    monkeypatch.setenv("FORECAST_MODE", "f1-center")
    candidate = tmp_path / "candidate" / "forecast.parquet"
    assert cli.main([*args, "--out", str(candidate)]) == 0
    if card["metadata"]["category"] == "T2-F1":
        assert base.read_bytes() != candidate.read_bytes()
        assert json.loads((candidate.parent / "forecast_meta.json").read_text())[
            "forecast_adjustment_applied"
        ]
    else:
        assert base.read_bytes() == candidate.read_bytes()
        assert pd.read_parquet(base).equals(pd.read_parquet(candidate))
