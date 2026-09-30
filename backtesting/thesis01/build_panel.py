"""## Executive summary (read this first)

Freeze the 25-asset public-panel universe on a business-day grid. Build daily
innovation scales and both contemporaneous and lag-safe cross-market tension.
Future outcomes remain in a private, outside-repository research ledger.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from qfbench2_track_forecasting.thesis01.asset_semantics import load_universe
from qfbench2_track_forecasting.thesis01.innovations import innovations
from qfbench2_track_forecasting.thesis01.scaling import scaled
from qfbench2_track_forecasting.thesis01.tension import at
from qfbench2_track_forecasting.v12.data_parity import _label
from qfbench2_track_forecasting.v12.joint_dataset import HORIZONS


def build(root: Path, private_out: Path) -> dict:
    if private_out.resolve().is_relative_to(root.resolve()):
        raise ValueError("Future labels must stay outside the public repository")
    series, kinds, first = load_universe(root)
    assets = sorted(series)
    # Frozen before outcome or score inspection. The 2024 factor prefix ends in
    # May, so 2023 is the last complete origin year common to the core groups.
    dates = pd.bdate_range("2000-01-03", "2024-12-18")
    panel = pd.DataFrame({a: series[a].reindex(dates) for a in assets}, index=dates)
    z_frame, sigma_frame = scaled(innovations(panel, kinds))
    z, sigma = z_frame.to_numpy(), sigma_frame.to_numpy()
    dense_same = np.full_like(z, np.nan)
    dense_lag = np.full_like(z, np.nan)
    for row, date in enumerate(dates):
        if date < pd.Timestamp("2001-01-02"):
            continue
        dense_same[row] = at(z, row, lag=0)
        dense_lag[row] = at(z, row, lag=1)
    origin_grid = pd.bdate_range("2001-01-02", "2023-12-29")[::21]
    grid_rows = dates.get_indexer(origin_grid)
    labels = np.full((len(grid_rows), len(assets), len(HORIZONS)), np.nan)
    target_end = np.full(labels.shape, np.datetime64("NaT"), dtype="datetime64[ns]")
    for o, row in enumerate(grid_rows):
        date = dates[row]
        for a, asset in enumerate(assets):
            for h, horizon in enumerate(HORIZONS):
                answer = _label(series[asset], kinds[asset], date, horizon,
                                "2100-01-01", False)
                if answer is not None and answer[1] <= pd.Timestamp("2024-12-18"):
                    labels[o, a, h], target_end[o, a, h] = answer
    q = labels / (sigma[grid_rows, :, None] * np.sqrt(np.asarray(HORIZONS))[None, None, :])
    private_out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(private_out, dates=dates.to_numpy(), origins=origin_grid.to_numpy(),
                        assets=np.asarray(assets), kinds=np.asarray([kinds[a] for a in assets]),
                        z=z, sigma=sigma, same=dense_same, lag=dense_lag,
                        grid_rows=grid_rows, native=labels, normalized=q, target_end=target_end,
                        first_target=np.asarray([first[a] for a in assets]))
    return {"assets": assets, "kinds": kinds, "first_target": first,
            "daily_start": str(dates[0].date()), "daily_end": str(dates[-1].date()),
            "origin_start": str(origin_grid[0].date()), "origin_end": str(origin_grid[-1].date()),
            "sparse_origins": len(origin_grid), "valid_labels": int(np.isfinite(labels).sum()),
            "dense_same_signals": int(np.isfinite(dense_same).sum()),
            "dense_lag_signals": int(np.isfinite(dense_lag).sum())}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--private-out", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(build(args.root, args.private_out), indent=2))
