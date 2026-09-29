"""Precommitted alphabetical 6-per-family public revised-history proxy.

This is a NEW 24-card diagnostic, not the missing archived pseudo-origin ledger.
Only grouped aggregates go into Git; private per-card realized scores stay outside.
"""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib

import numpy as np
import pandas as pd
from qfbench2_common.scoring import crps

from qfbench2_track_forecasting.tail import tail_pinball
from qfbench2_track_forecasting.v12.train import load_public_panels
from qfbench2_track_forecasting.v13.engine import CopulaEngine


def eligible(unit: Path, history: pd.DataFrame):
    card = tomllib.loads((unit / "card.toml").read_text())
    target = card["targets"]
    if target.get("target_frequency", "daily") != "daily":
        return None
    asof = pd.Timestamp(card["provenance"]["data_cutoff"])
    assets, horizons = target["asset_ids"], list(map(int, target["horizons"]))
    if any(a not in history for a in assets):
        return None
    i = history.index.searchsorted(asof, side="right") - 1
    if i < 0 or i + max(horizons) >= len(history):
        return None
    anchor = history.iloc[i][assets].to_numpy(dtype=float)
    truth = np.array([[history.iloc[i+h][a] for a in assets] for h in horizons], dtype=float)
    if not np.isfinite(anchor).all() or not np.isfinite(truth).all():
        return None
    if target.get("target_type") == "log_return":
        truth -= anchor[None, :]
    return card, assets, horizons, truth


def component_scores(samples: np.ndarray, truth: np.ndarray):
    x = samples.reshape(len(samples), -1)
    y = truth.reshape(-1)
    return {"marginal": float(crps.crps_marginal(x, y)),
            "joint": float(crps.variogram_score(x, y, p=.5)) if len(y) > 1 else None,
            "tail": float(tail_pinball(x, y, (.01, .05, .95, .99)))}


def geometric(values):
    return float(np.exp(np.mean(np.log(np.maximum(values, 1e-12))))) if values else None


def grouped(rows: list[dict]) -> dict:
    if not rows:
        return {"cases": 0}
    return {"cases": len(rows),
            "overall_ratio": geometric([r["composite_ratio"] for r in rows]),
            "marginal_ratio_median": float(np.median([r["marginal_ratio"] for r in rows])),
            "joint_ratio_median": float(np.median([r["joint_ratio"] for r in rows
                                                   if r["joint_ratio"] is not None]))
                                  if any(r["joint_ratio"] is not None for r in rows) else None,
            "tail_ratio_median": float(np.median([r["tail_ratio"] for r in rows])),
            "win_rate": float(np.mean([r["composite_ratio"] < 1 for r in rows]))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--units", type=Path, default=Path("units"))
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--bank", type=Path)
    p.add_argument("--private-out", type=Path, required=True)
    p.add_argument("--public-out", type=Path, required=True)
    p.add_argument("--draws", type=int, default=2000)
    a = p.parse_args()
    if a.private_out.resolve().is_relative_to(Path.cwd()):
        raise SystemExit("Per-card outcomes must stay outside the Git repository")
    panel, _ = load_public_panels(a.units)
    history = panel.pivot(index="date", columns="asset", values="value").sort_index()
    engine = CopulaEngine(a.artifact, a.bank)
    chosen = []
    for family in ("F1", "F2", "F3", "F4"):
        candidates = []
        for unit in sorted(a.units.glob(f"t2-{family}-*/")):
            if (unit / "card.toml").exists():
                info = eligible(unit, history)
                if info is not None:
                    candidates.append((unit, info))
        if len(candidates) < 6:
            raise ValueError(f"Insufficient public outcome coverage for {family}")
        chosen.extend(candidates[:6])  # frozen before any model score is read
    rows = []
    for n, (unit, (card, assets, horizons, truth)) in enumerate(chosen):
        asof = card["provenance"]["data_cutoff"]
        with tempfile.TemporaryDirectory() as tmp:
            forecast = Path(tmp) / "forecast.parquet"
            cmd = [sys.executable, "-m", "qfbench2_track_forecasting.cli",
                   "--panels", str(unit), "--text", str(unit / "text"),
                   "--asof", asof, "--out", str(forecast),
                   "--n-draws", str(a.draws), "--seed", "19"]
            env = os.environ.copy(); env["FORECAST_MODE"] = "text-first-v5.1"
            subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
            result = pd.read_parquet(forecast)
            draws = sorted(result.draw.unique())
            index = pd.MultiIndex.from_product([draws, assets, horizons],
                                               names=["draw", "asset", "horizon"])
            baseline = result.set_index(["draw", "asset", "horizon"]).value.reindex(index)
            if baseline.isna().any():
                raise ValueError("Missing baseline draw cell")
            baseline = baseline.to_numpy().reshape(len(draws), len(assets), len(horizons)).transpose(0,2,1)
        inputs = pd.concat([pd.read_parquet(f) for f in unit.glob("*.parquet")], ignore_index=True)
        outputs, meta = engine.forecast(baseline, inputs, assets, horizons, asof,
                                        card["targets"].get("target_type", "level"),
                                        card["targets"].get("target_frequency", "daily"), 19)
        reference = component_scores(baseline, truth)
        for name, values in outputs.items():
            comp = component_scores(values, truth)
            m = comp["marginal"] / max(reference["marginal"], 1e-12)
            t = comp["tail"] / max(reference["tail"], 1e-12)
            j = comp["joint"] / max(reference["joint"], 1e-12) if comp["joint"] is not None else None
            ratio = (0.5*m + 0.3*j + 0.2*t) if j is not None else (0.5*m + 0.2*t)/0.7
            rows.append({"card": unit.name, "family": card["metadata"]["category"],
                         "year": int(str(asof)[:4]), "postfit": str(asof) >= "2009-10-01",
                         "cells": len(assets)*len(horizons), "candidate": name,
                         "marginal_ratio": m, "joint_ratio": j, "tail_ratio": t,
                         "composite_ratio": ratio, "fallback": meta.get("fallback")})
        print(f"{n+1}/24 {unit.name}", flush=True)
    a.private_out.parent.mkdir(parents=True, exist_ok=True)
    a.private_out.write_text(json.dumps(rows, indent=2) + "\n")
    public = {"kind":"NEW_REVISED_HISTORY_PROXY_NOT_ARCHIVED_RUN",
              "draws":a.draws,"cases":24,"selection":"first six alphabetical eligible public cards per family, fixed before scoring",
              "source":"current revised public panel prefixes; not verified PIT",
              "models":{name:{"overall":grouped([r for r in rows if r["candidate"]==name]),
                              "family":{fam:grouped([r for r in rows if r["candidate"]==name and r["family"]==fam])
                                        for fam in ("T2-F1","T2-F2","T2-F3","T2-F4")},
                              "postfit":grouped([r for r in rows if r["candidate"]==name and r["postfit"]]),
                              "single":grouped([r for r in rows if r["candidate"]==name and r["cells"]==1]),
                              "multi":grouped([r for r in rows if r["candidate"]==name and r["cells"]>1])}
                        for name in "ABC"}}
    a.public_out.parent.mkdir(parents=True, exist_ok=True)
    a.public_out.write_text(json.dumps(public, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"cases":24,"postfit":public["models"]["A"]["postfit"]["cases"],
                      "A_overall":public["models"]["A"]["overall"]["overall_ratio"]}))


if __name__ == "__main__":
    main()
