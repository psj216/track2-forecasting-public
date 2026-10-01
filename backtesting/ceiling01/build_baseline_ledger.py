"""## Executive summary (read this first)

Prepare the fixed V13 24-card universe and verify SURPRISE's archived caches.
Store all outcomes and native baseline arrays outside Git. Do not score oracles.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from backtesting.v13_copula.evaluate_proxy import eligible
from qfbench2_track_forecasting.cli import _draw, _read_panels, _series
from qfbench2_track_forecasting.text_first_v5 import apply_text_first_v5
from qfbench2_track_forecasting.v12.train import load_public_panels
from qfbench2_track_forecasting.ceiling01.coverage_bounds import classify


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def card_draws(unit, card, text=True):
    target = card["targets"]
    assets, horizons = target["asset_ids"], list(map(int, target["horizons"]))
    asof = str(card["provenance"]["data_cutoff"])
    kind, frequency = target.get("target_type", "level"), target.get("target_frequency", "daily")
    family = card["metadata"]["category"]
    os.environ["NUMERIC_VARIANT"] = "v3"
    os.environ["FORECAST_MODE"] = "text-first-v5.1"
    panels = _read_panels(unit)
    raw, _ = _draw(panels, assets, horizons, asof, 2000, 19, kind, frequency, family)
    if not text:
        return raw.transpose(0, 2, 1)
    values, _ = apply_text_first_v5(raw,
        {a: _series(panels, a, asof) for a in assets} if family in {"T2-F1", "T2-F4"} else {},
        assets, horizons, kind, frequency, family, asof, 19, unit / "text",
        str(target.get("value_unit", "")), interpreter_version="v5.1")
    return values.transpose(0, 2, 1)


def prepare(root, private, surprise):
    if private.resolve().is_relative_to(root.resolve()) or surprise.resolve().is_relative_to(root.resolve()):
        raise ValueError("Private paths must be outside the repository")
    private.mkdir(parents=True, exist_ok=True)
    panel, _ = load_public_panels(root / "units")
    history = panel.pivot(index="date", columns="asset", values="value").sort_index()
    artifact = json.loads((root / "qfbench2_track_forecasting/v12/artifacts_v13_r2.json").read_text())
    selected = []
    for fam in ("F1", "F2", "F3", "F4"):
        choices = []
        for unit in sorted((root / "units").glob(f"t2-{fam}-*/")):
            info = eligible(unit, history)
            if info is not None:
                choices.append((unit, info))
        if len(choices) < 6:
            raise ValueError(f"Insufficient cards: {fam}")
        selected += choices[:6]
    records = []
    for i, (unit, (card, assets, horizons, truth)) in enumerate(selected):
        baseline = card_draws(unit, card)
        numeric = card_draws(unit, card, text=False)
        path = private / f"card-{i:02}.npz"
        np.savez_compressed(path, baseline=baseline, numeric=numeric, truth=truth)
        target = card["targets"]
        support = classify(artifact, assets, target.get("target_type", "level"),
                           target.get("target_frequency", "daily"))
        support["single_cell"] = np.size(truth) == 1
        records.append({"id": unit.name, "family": card["metadata"]["category"],
                        "origin": str(card["provenance"]["data_cutoff"]),
                        "assets": assets, "horizons": horizons, "cells": int(np.size(truth)),
                        "target_type": target.get("target_type", "level"),
                        "frequency": target.get("target_frequency", "daily"),
                        "file": path.name, "sha256": digest(path), "support": support})
        print(f"prepared baseline {i+1}/24", flush=True)
    dump(private / "cards.json", records)
    frozen = json.loads((root / "backtesting/surprise01/frozen_inputs.json").read_text())
    cases_path = surprise / "training_cases.parquet"
    if digest(cases_path) != frozen["case_sha256"]:
        raise ValueError("SURPRISE cases differ from frozen input")
    cases = pd.read_parquet(cases_path)
    eval_cases = cases[(cases.origin >= "2017-01-01") & (cases.origin <= "2024-12-18")]
    if (eval_cases.target_end >= "2025-01-01").any():
        raise ValueError("2025 outcomes forbidden")
    cache_hashes = {}
    for file in sorted(eval_cases.cache_file.unique()):
        h = digest(surprise / "draw_cache" / file)
        if h != frozen["draw_cache_sha256"][file]:
            raise ValueError(f"Archive cache mismatch: {file}")
        cache_hashes[file] = h
    manifest = {
        "status": "PRE_SCORE_INPUT_FREEZE", "scorer_status": "RESEARCH_PROXY_ONLY",
        "parent_sha": "31ab7cd70020d0c2d55df6e7e767fa91de98fffc",
        "card_universe": {"name": "V13_REVISED_PUBLIC_24", "cards": 24,
            "cells": sum(r["cells"] for r in records),
            "single": sum(r["cells"] == 1 for r in records),
            "multi": sum(r["cells"] > 1 for r in records),
            "ledger_sha256": digest(private / "cards.json"),
            "files": {r["file"]: r["sha256"] for r in records},
            "date_range": [min(r["origin"] for r in records), max(r["origin"] for r in records)],
            "selection": "same first six alphabetical eligible cards per family as V13 reconstruction",
            "draws": 2000, "seed": 19},
        "surprise_universe": {"name": "SURPRISE_EXPOSED_MARGINAL_ONLY", "cells": len(eval_cases),
            "origins": int(eval_cases.origin.nunique()), "events": int(eval_cases.event_id.nunique()),
            "date_range": [eval_cases.origin.min(), eval_cases.origin.max()],
            "case_sha256": digest(cases_path), "cache_sha256": cache_hashes,
            "metric": "arithmetic mean volatility-normalized marginal fair CRPS only"},
        "unavailable": {"original_V12_V13_pseudo_origins": "only archived aggregate JSON available; not recreated as original",
                        "THESIS_ORIGIN": "grouped metrics audited; private label/draw ledgers not present; not merged"},
        "method": {"location": "truth-minus-median additive shift",
            "scale": "exact convex fair-CRPS minimizer; nonnegative and [0.5,2] separately",
            "tail": "outer-quartile monotone truth projection, central interpolation supports preserved",
            "joint": "3 fixed starts, 12000 greedy swaps each, seed1901; feasible not global optimum",
            "structured": "leave-one-calendar-era-out group/horizon correction; exposed only",
            "eras": "<=2016,2017-2019,2020-2021,2022-2024",
            "feasibility": "uniform component fractional replacements via actual research aggregation"}}
    dump(root / "backtesting/ceiling01/frozen_inputs.json", manifest)
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--private", type=Path, required=True)
    p.add_argument("--surprise", type=Path, required=True)
    a = p.parse_args()
    prepare(a.root, a.private, a.surprise)
