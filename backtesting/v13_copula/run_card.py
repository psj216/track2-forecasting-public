"""Run the real V5.1 CLI, then reconstruct V13 A/B/C against its rank worlds."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.v13.engine import CopulaEngine


def run(unit: Path, artifact: Path, bank: Path | None, out: Path,
        candidate: str, draws: int, seed: int) -> dict:
    card = tomllib.loads((unit / "card.toml").read_text())
    target = card["targets"]
    assets, horizons = list(target["asset_ids"]), list(map(int, target["horizons"]))
    asof = card["provenance"]["data_cutoff"]
    frames = [pd.read_parquet(path) for path in unit.glob("*.parquet")]
    panel = pd.concat(frames, ignore_index=True)
    with tempfile.TemporaryDirectory() as tmp:
        baseline_path = Path(tmp) / "forecast.parquet"
        command = [sys.executable, "-m", "qfbench2_track_forecasting.cli", "--panels", str(unit),
                   "--text", str(unit / "text"), "--asof", asof, "--out", str(baseline_path),
                   "--n-draws", str(draws), "--seed", str(seed)]
        env = os.environ.copy(); env["FORECAST_MODE"] = "text-first-v5.1"
        subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        frame = pd.read_parquet(baseline_path)
        draws_actual = sorted(frame.draw.unique())
        index = pd.MultiIndex.from_product([draws_actual, assets, horizons],
                                           names=["draw", "asset", "horizon"])
        baseline = frame.set_index(["draw", "asset", "horizon"]).value.reindex(index)
        if baseline.isna().any():
            raise ValueError("V5.1 world tensor has missing cells")
        v51 = baseline.to_numpy().reshape(len(draws_actual), len(assets), len(horizons)).transpose(0, 2, 1)
        output, metadata = CopulaEngine(artifact, bank).forecast(
            v51, panel, assets, horizons, asof, target.get("target_type", "level"),
            target.get("target_frequency", "daily"), seed)
        chosen = output[candidate]
        lookup = {(d, asset, h): chosen[i, j, k]
                  for i,d in enumerate(draws_actual) for j,h in enumerate(horizons)
                  for k,asset in enumerate(assets)}
        frame["value"] = [lookup[(row.draw, row.asset, row.horizon)]
                          for row in frame.itertuples(index=False)]
        out.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(out / "forecast.parquet", index=False)
        sidecar = json.loads((Path(tmp) / "forecast_meta.json").read_text())
        sidecar["reconstructed_engine"] = "V13-" + candidate
        sidecar["reconstruction_fallback"] = metadata.get("fallback")
        (out / "forecast_meta.json").write_text(json.dumps(sidecar, indent=2))
        (out / "forecast_rationale.md").write_text(
            (Path(tmp) / "forecast_rationale.md").read_text() +
            "\n\nV13 reconstructed copula experiment. Archived original coefficients unavailable.\n")
    return {"card": unit.name, "family": card["metadata"]["category"],
            "shape": list(chosen.shape), "finite": bool(np.isfinite(chosen).all()),
            "fallback": metadata.get("fallback"), "reason": metadata.get("reason"),
            "bank_used": metadata.get("bank_used", False),
            "marginals_identical_abc": all(np.array_equal(np.sort(chosen, axis=0),
                                                       np.sort(output[name], axis=0)) for name in "ABC")}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--unit", type=Path, required=True)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--bank", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--candidate", choices=list("ABC"), default="A")
    p.add_argument("--draws", type=int, default=500)
    p.add_argument("--seed", type=int, default=19)
    a = p.parse_args()
    print(json.dumps(run(a.unit, a.artifact, a.bank, a.out,
                         a.candidate, a.draws, a.seed), indent=2))


if __name__ == "__main__":
    main()
