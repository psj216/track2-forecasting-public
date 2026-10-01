"""## Executive summary (read this first)

Build five-business-day historical fit rows with 2023-mature labels only.
Source shocks are yesterday's; target gates are observed at each origin.
The private matrix stays outside the repository.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.origin01 import HORIZONS, TRAINING_CUTOFF
from qfbench2_track_forecasting.origin01.shock_detector import excess
from qfbench2_track_forecasting.origin01.unreacted_gate import unreacted
from qfbench2_track_forecasting.thesis01.asset_semantics import load_universe
from qfbench2_track_forecasting.v12.data_parity import _label


def build(root: Path, panel_path: Path, output: Path):
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError("Individual training labels must remain outside Git")
    panel = np.load(panel_path)
    assets = panel["assets"].tolist()
    z, sigma = panel["z"], panel["sigma"]
    dates = pd.DatetimeIndex(panel["dates"])
    historical = pd.bdate_range("2001-01-02", "2023-12-29")[::5]
    rows = dates.get_indexer(historical)
    if np.any(rows < 1):
        raise ValueError("Missing source date")
    # Explicitly truncate every asset before calling the label constructor.
    raw, kinds, _ = load_universe(root)
    history = {a: raw[a].loc[:pd.Timestamp(TRAINING_CUTOFF)] for a in assets}
    x = excess(z[rows - 1])
    gate = unreacted(z[rows])
    q = np.full((len(rows), len(assets), len(HORIZONS)), np.nan)
    ends = np.full(q.shape, np.datetime64("NaT"), dtype="datetime64[ns]")
    cutoff = pd.Timestamp(TRAINING_CUTOFF)
    for o, date in enumerate(historical):
        for i, asset in enumerate(assets):
            if not gate[o, i] or not np.isfinite(sigma[rows[o], i]):
                continue
            for h, horizon in enumerate(HORIZONS):
                result = _label(history[asset], kinds[asset], date, horizon,
                                "2100-01-01", False)
                if result is None or result[1] > cutoff:
                    continue
                q[o, i, h] = result[0] / (sigma[rows[o], i] * np.sqrt(horizon))
                ends[o, i, h] = result[1]
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, dates=historical.to_numpy(), assets=np.asarray(assets),
                        horizons=np.asarray(HORIZONS), source=x, gate=gate, q=q,
                        target_end=ends)
    return {"origins": len(rows), "assets": len(assets),
            "mature_cells": int(np.isfinite(q).sum()),
            "active_source_rows": int((np.abs(x).sum(axis=1) > 0).sum()),
            "date_start": str(historical[0].date()), "date_end": str(historical[-1].date()),
            "max_target_end": str(pd.to_datetime(ends[~np.isnat(ends)]).max().date())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--private-out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.panel, args.private_out), indent=2))
