"""Smoke four public family cards against the newly fitted artifact."""

import argparse
import json
from pathlib import Path
import tomllib
import pandas as pd

from qfbench2_track_forecasting.v12.engine import JointEngine


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--units", type=Path, default=Path("units"))
    p.add_argument("--draws", type=int, default=500)
    a = p.parse_args()
    engine = JointEngine(a.artifact)
    results = []
    for family in ("F1", "F2", "F3", "F4"):
        for folder in sorted(a.units.glob(f"t2-{family}-*/")):
            card = tomllib.loads((folder / "card.toml").read_text())
            assets = card["targets"]["asset_ids"]
            if any(asset not in engine.artifact["assets"] for asset in assets):
                continue
            files = list(folder.glob("*.parquet"))
            if not files:
                continue
            panel = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
            asof = card["provenance"]["data_cutoff"]
            try:
                output, meta = engine.forecast(panel, assets, card["targets"]["horizons"],
                                               asof, a.draws, 19,
                                               card["targets"].get("target_type", "level"))
            except (ValueError, KeyError):
                continue
            results.append(dict(family=family, card=folder.name, shape=list(output.shape),
                                finite=bool(pd.notna(output).all()), metadata=meta))
            break
    print(json.dumps(results, indent=2))
    if {r["family"] for r in results} != {"F1", "F2", "F3", "F4"}:
        raise SystemExit("Not all four public family structures were exercised")


if __name__ == "__main__":
    main()
