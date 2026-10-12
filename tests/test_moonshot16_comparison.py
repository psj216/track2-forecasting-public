"""## Executive summary (read this first)
Compare frozen M15 and repaired M15 on identical public inputs and synthetic replies.
This measures runtime/forecast equivalence, never independent prediction quality.
"""

from __future__ import annotations

import hashlib
import json
import os
import tomllib
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from test_moonshot16_runtime import ROOT, grant, mock_route as mock_route

from moonshot15_engine import cli


def frozen_module(name, source, digest):
    raw = source.encode()
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == digest
    module = types.ModuleType("moonshot15_engine.frozen_" + name)
    module.__package__ = "moonshot15_engine"
    module.__file__ = str(ROOT / "moonshot15_engine" / (name + ".py"))
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


@pytest.mark.parametrize("variant", list("ABCDE"))
@pytest.mark.parametrize("unit_name", ["t2-F1-patient-dropped-2015", "t2-F3-brexit-joint-2016"])
def test_public_original_repaired_baseline(variant, unit_name, mock_route, monkeypatch, tmp_path):
    frozen = json.loads((ROOT / "tests/fixtures/moonshot16_frozen_source.json").read_text())
    old_transport = frozen_module(
        "official_transport",
        frozen["official_transport_source"],
        frozen["official_transport_blob_sha"],
    )
    old_engine = frozen_module("engine", frozen["engine_source"], frozen["engine_blob_sha"])
    old_cli = frozen_module("cli", frozen["cli_source"], frozen["cli_blob_sha"])
    old_engine._house_reply = old_transport._house_reply
    old_cli.request, old_cli.transform = old_engine.request, old_engine.transform
    unit = ROOT / "units" / unit_name
    asof = str(tomllib.loads((unit / "card.toml").read_text())["provenance"]["data_cutoff"])
    args = [
        "--panels",
        str(unit),
        "--text",
        str(unit / "text"),
        "--asof",
        asof,
        "--card",
        str(unit / "card.toml"),
        "--out",
    ]
    results, metadata = {}, {}
    for label, main, case in [
        ("original_normal", old_cli.main, "lowercase_only"),
        ("repaired_normal", cli.main, "lowercase_only"),
        ("original_uppercase", old_cli.main, "uppercase_only"),
        ("repaired_uppercase", cli.main, "uppercase_only"),
        ("V51_fallback", cli.main, "endpoint_missing"),
    ]:
        grant(monkeypatch, mock_route, variant, case)
        folder = tmp_path / label
        folder.mkdir()
        assert main([*args, str(folder / "forecast.parquet")]) == 0
        results[label] = (folder / "forecast.parquet").read_bytes()
        metadata[label] = json.loads((folder / "forecast_meta.json").read_text())["moonshot15"]
        if label == "original_uppercase":
            assert mock_route.calls == 0
    assert results["original_normal"] == results["repaired_normal"] == results["repaired_uppercase"]
    assert results["original_uppercase"] == results["V51_fallback"]
    assert results["repaired_normal"] != results["V51_fallback"]
    assert metadata["original_normal"]["geometry"] == metadata["repaired_normal"]["geometry"]
    frame = pd.read_parquet(tmp_path / "repaired_normal/forecast.parquet")
    base = pd.read_parquet(tmp_path / "V51_fallback/forecast.parquet")
    assert frame.shape == base.shape and np.isfinite(frame["value"]).all()
    assert np.array_equal(frame[["draw", "asset", "horizon"]], base[["draw", "asset", "horizon"]])
    wide = frame.pivot(index="draw", columns=["asset", "horizon"], values="value")
    comparison = {
        "executive_summary": "Public-input synthetic comparison; no realized targets or quality claim.",
        "unit": unit_name,
        "variant": variant,
        "passed": True,
        "original_normal_equals_repaired_normal": True,
        "uppercase_repair_changes_original_fallback": True,
        "row_count": len(frame),
        "draw_shape": list(wide.shape),
        "finite": True,
        "mean": wide.mean().tolist(),
        "standard_deviation": wide.std(ddof=0).tolist(),
        "geometry": metadata["repaired_normal"]["geometry"],
        "old_and_new_cross_asset_and_horizon_distribution": "BYTE_IDENTICAL",
        "forecast_SHA256": {k: hashlib.sha256(v).hexdigest() for k, v in results.items()},
    }
    if os.environ.get("M16_COMPARISON_DIR"):
        folder = Path(os.environ["M16_COMPARISON_DIR"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{variant}-{unit_name}.json").write_text(json.dumps(comparison, indent=2) + "\n")
