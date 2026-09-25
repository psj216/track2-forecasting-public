"""## Executive summary (read this first)

Prove the full CLI makes real localhost HTTP requests for F2 and F4, accepts
minimal grounded JSON, and changes forecasts relative to frozen Numeric V3.
A stand-in transport cannot establish actual Nemotron behavior.
"""

from __future__ import annotations

import json

from backtesting.activation_probe import UNITS, local_house, run


def test_full_http_path_activates_f2_and_f4(tmp_path, monkeypatch):
    for name in ("NUMERIC_VARIANT", "F1_CALIBRATION_PATH", "TEXT_INTEGRATION"):
        monkeypatch.delenv(name, raising=False)
    with local_house():
        results = run(tmp_path / "activation", "mock", UNITS)
    assert {row["family"] for row in results if row["passed"]} == {"T2-F2", "T2-F4"}
    assert all(row["router"]["samples_changed"] for row in results)
    assert all(row["samples_differ"] for row in results)
    assert (
        json.loads((tmp_path / "activation" / "activation-results.json").read_text())["mode"]
        == "mock"
    )
