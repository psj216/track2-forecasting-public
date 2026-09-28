"""## Executive summary (read this first)

Verify the opt-in tail mode changes only single-cell non-F3 draws, after V5.1.
The scored output and metadata must agree about text and tail activation.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd
import pytest

from qfbench2_track_forecasting.cli import main


@pytest.mark.parametrize(
    ("unit", "expected_change"),
    [
        ("t2-F2-time-has-come-2024", True),
        ("t2-F4-short-vol-2018", True),
        ("t2-F1-greater-confidence-2024", False),
        ("t2-F3-brexit-joint-2016", False),
    ],
)
def test_tail_mode_preserves_v51_except_single_cell(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, unit: str, expected_change: bool
) -> None:
    root = pathlib.Path(__file__).parents[1] / "units" / unit
    if not root.is_dir():
        pytest.skip("unit is not part of this public checkout")
    import tomllib

    card = tomllib.loads((root / "card.toml").read_text())
    outputs = {}
    for mode in ("text-first-v5.1", "text-first-v5.1-tail"):
        monkeypatch.setenv("FORECAST_MODE", mode)
        path = tmp_path / mode / "forecast.parquet"
        assert (
            main(
                [
                    "--panels",
                    str(root / "panels"),
                    "--text",
                    str(root / "text"),
                    "--asof",
                    card["provenance"]["data_cutoff"],
                    "--n-draws",
                    "1000" if card["metadata"]["category"] == "T2-F4" else "500",
                    "--seed",
                    "29",
                    "--out",
                    str(path),
                ]
            )
            == 0
        )
        outputs[mode] = (
            pd.read_parquet(path),
            json.loads((path.parent / "forecast_meta.json").read_text()),
        )
    base, base_meta = outputs["text-first-v5.1"]
    tail, tail_meta = outputs["text-first-v5.1-tail"]
    assert (not base.equals(tail)) == expected_change
    assert tail_meta["reasoning_applied"] == base_meta["reasoning_applied"]
    if expected_change:
        baseline = base["value"].to_numpy()
        changed = tail["value"].to_numpy()
        lo, hi = np.quantile(baseline, [0.1, 0.9])
        np.testing.assert_allclose(
            changed[(baseline >= lo) & (baseline <= hi)],
            baseline[(baseline >= lo) & (baseline <= hi)],
        )
        assert tail_meta["rationale"]["scenario_integration"]["tail_applied"] is True
    else:
        assert tail_meta["rationale"]["scenario_integration"]["tail_applied"] is False
